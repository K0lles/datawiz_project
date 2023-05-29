import datetime
import operator
from datetime import timedelta
from typing import Optional, Type

import pandas as pd
from django.db.models import Model
from django.utils.translation import gettext_lazy as _
from pydantic import BaseModel
from rest_framework.exceptions import ValidationError

from analytics import dimensions as dm
from analytics.constants import (DIFF, MAX_DATE_COLUMNS, MIN_DATE_COLUMNS,
                                 NON_BILLABLE_COLUMNS, PERCENT)
from analytics.metrics import ModelMetric
from analytics.models import (DimensionEnum, IntervalEnum, MetricModelsEnum,
                              MetricNameEnum)
from analytics.serializers import (DateRangeBaseModel,
                                   DimensionQualifierBaseModel,
                                   MetricsOverallBaseModel)
from receipts.models import CartItem


class BaseMainAggregator:
    dimension_aggregator_class = None
    metric_aggregator_class = None
    date_range_aggregator_class = None
    dataframe_aggregator_class = None
    model_name = None   # basing model queries will be made

    def __init__(self, dimensions: list, metrics: list, date_range: list, prev_date_range: list = None):
        if not self.dimension_aggregator_class \
                or not self.metric_aggregator_class \
                or not self.date_range_aggregator_class \
                or not self.dataframe_aggregator_class \
                or not self.model_name:
            raise AttributeError(f"Base class fields are not defined in {self.__class__.__name__}.")

        self.dimensions: list[dict] = dimensions
        self.metrics_data: list[dict] = metrics
        self.date_range: list[str, str] = date_range
        self.prev_date_range: Optional[list[str, str]] = prev_date_range

        # fields for dimensions
        self.pre_annotation: dict = {}
        self.pre_values: list = []
        self.pre_filtering: dict = {}
        self.parsing_fields: dict = {}

        self.has_intervals: bool = False

        # fields for metrics
        self.main_annotation: dict = {}
        self.adapted_annotation: dict = {}
        self.post_filtering: dict = {}
        self.adapted_post_filtering: dict = {}

        self.dataframe_filtering = {}

        self.required_previous_date_range: bool = False

        # fields for date_ranges
        self.date_pre_filtering: dict | None = None
        self.date_previous_pre_filtering: dict | None = None


class DimensionAggregator:
    interval_base_models = ['IntervalBaseModel']

    def __init__(self, dimension_data: list, main_agg: BaseMainAggregator):
        self.dimension_data = dimension_data
        self.agg = main_agg

        self.validate_dimensions()

    def get_dimension_base_model(self, dimension_name: str) -> None:
        self.dimension_base_model: Type[BaseModel] = DimensionQualifierBaseModel(name=dimension_name).dict()['name']
        self.agg.has_intervals = True if self.dimension_base_model.__name__ == 'IntervalBaseModel' \
            else self.agg.has_intervals

    def validate_dimensions(self) -> None:
        """
        Validates data from dimension dictionary.
        """
        for unit_date in self.dimension_data:
            self.get_dimension_base_model(unit_date.get('name'))
            dimension_answer: dict = self.dimension_base_model(**unit_date).dict()
            self.set_dimension_answers(dimension_answer)

    def set_dimension_answers(self, dimension_answer: dict) -> None:
        if self.dimension_base_model.__name__ not in self.interval_base_models:
            dimension_class: Type[dm.DimensionFieldAssignment] = \
                getattr(dm, f'{dimension_answer.get("name")}FieldAssignment')

            answer = dimension_class(**dimension_answer).response()
        else:
            answer = dimension_answer

        self.agg.pre_annotation.update(answer.get('pre_annotation', {}))
        self.agg.pre_filtering.update(answer.get('pre_filtering', {}))
        self.agg.pre_values.extend(answer.get('pre_values', []))
        self.agg.parsing_fields.update(answer.get('parsed_field_names', {}))


class MetricAggregator:

    def __init__(self, metrics: list, model_name: type[Model], main_agg: BaseMainAggregator):
        self.metrics_data: list = metrics
        self.model_name: type[Model] = model_name

        self.agg = main_agg

        # is used when validating model metrics. Not for outer scope usage
        self.model_metric: type[ModelMetric | None] = None

        self.set_metric_validation_model()
        self.validate_metric_answers()

    def set_metric_validation_model(self) -> None:
        """
        Defines which metric class must be used for current metric
        parameter
        """
        self.model_metric: Type[ModelMetric] = MetricModelsEnum.get_metric_model_by_name(self.model_name.__name__)

    def validate_metric_answers(self) -> None:
        """
        Iterates through each item in annotation part of
        metrics and parse it for use in query directly
        """
        metric_answer: dict = MetricsOverallBaseModel(metrics=self.metrics_data).dict()

        # variable for correct setting of 'product_article' and 'product_barcode'
        has_product_dimension: bool = 'product' in [item['name'] for item in self.agg.dimensions]

        self.agg.required_previous_date_range = metric_answer.get('required_date_ranges', False)

        self.agg.dataframe_filtering = metric_answer.get('dataframe_filtering', {})

        for metric in metric_answer.get('post_filtering', []):
            parsed_metric_answers = self.model_metric(**metric, has_product_dimension=has_product_dimension).response()
            self.agg.main_annotation.update(parsed_metric_answers.get('annotation', {}))
            self.agg.post_filtering.update(parsed_metric_answers.get('post_filtering', {}))

        if self.agg.dataframe_filtering:
            self.adapt_annotations_and_filtering()

    def adapt_annotations_and_filtering(self) -> None:
        """
        Adapts post_filtering and main_annotation in order to make less
        queries in prev_daterange when there is no conditions to seek diff
        or diff_percent in several metrics
        """
        dataframe_names = []
        for element in self.agg.dataframe_filtering:
            dataframe_names.append(element['name'].replace(DIFF, '').replace(PERCENT, ''))

        for key, value in self.agg.main_annotation.items():
            if key in dataframe_names:
                self.agg.adapted_annotation[key] = value

        for key, value in self.agg.post_filtering.items():
            main_name = key.split('__')[0]
            if main_name in dataframe_names:
                self.agg.adapted_post_filtering[key] = value


class DateRangesAggregator:

    def __init__(self,
                 date_range: list,
                 prev_date_range: list,
                 main_agg: BaseMainAggregator):
        self.agg = main_agg
        self.date_ranges = {
            'date_range': date_range,
            'prev_date_range': prev_date_range,
            'previous': self.agg.required_previous_date_range
        }

        self.validate_date_ranges()

    def validate_date_ranges(self) -> None:
        """
        Validates date ranges and set to main aggregation class
        suitable for direct starring into queries ranges
        """
        date_range_answer: dict = DateRangeBaseModel(**self.date_ranges).dict()
        self.agg.date_pre_filtering = date_range_answer.get('pre_filtering')
        self.agg.date_previous_pre_filtering = date_range_answer.get('previous_pre_filtering', {})


class DataFrameAggregator:
    comparison_functions = {
        'exact': operator.eq,
        'exclude': operator.ne,
        'lt': operator.lt,
        'lte': operator.le,
        'gt': operator.gt,
        'gte': operator.ge,
    }

    def __init__(self, main_agg: BaseMainAggregator):

        self.agg = main_agg

    def get_interval_class(self) -> Type[IntervalEnum]:
        return IntervalEnum

    def get_timedelta(self, first_date: str, last_date: str) -> timedelta:
        return datetime.datetime.strptime(last_date, '%Y-%m-%d') - datetime.datetime.strptime(first_date, '%Y-%m-%d')

    def get_interval_field(self) -> str:
        return list(self.agg.pre_annotation.keys())[0]

    def apply_dataframe_without_common_fields(self,
                                              current_range_df: pd.DataFrame,
                                              prev_range_df: pd.DataFrame) -> pd.DataFrame:
        """
        Evaluated dataframes with common fields
        """

        # drops indexes in order to get all records be able to subtract
        current_range_df.reset_index(drop=True, inplace=True)
        prev_range_df.reset_index(drop=True, inplace=True)

        for obj in self.agg.dataframe_filtering:
            name: str = obj.get('name')
            existing_name = name.replace(DIFF, '').replace(PERCENT, '')

            # Calculate the 'field_diff' by subtracting 'field' from the previous DataFrame
            if 'percent' in name:
                current_range_df[name] = round(self.find_percent(
                    current_range_df[existing_name], prev_range_df[existing_name]
                ), 2)
            else:
                current_range_df[name] = round(current_range_df[existing_name] - prev_range_df[existing_name], 2)

            # Fill NaN values in 'field_diff' with 'field' from the current DataFrame
            current_range_df[name].fillna(current_range_df[existing_name], inplace=True)

            # iterating through 'options' inside every field and applying them
            for filter_data in obj.get('options', {}):
                option = filter_data['option']
                value = filter_data['value']

                comparison_func = self.comparison_functions[option]

                # get comparison function in order to further filtration of df
                filter_condition = comparison_func(current_range_df[name], value)

                current_range_df = current_range_df[filter_condition]
        return current_range_df

    def apply_dataframe_with_common_fields(self,
                                           filtered_df: pd.DataFrame,
                                           common_fields: list,
                                           exception_fields: list) -> pd.DataFrame:
        """
        Evaluates all metric without having common fields (only interval dimensions)
        """
        dataframe_fields = []
        for obj in self.agg.dataframe_filtering:
            name: str = obj.get('name')
            dataframe_fields.append(name)
            existing_name = name.replace(DIFF, '').replace(PERCENT, '')

            # Calculate the 'field_diff' and 'field_diff_percent' by subtracting 'field' from the previous DataFrame
            if 'percent' in name:
                filtered_df[name] = round(self.find_percent(
                    filtered_df[existing_name], filtered_df[f'{existing_name}_prev']), 2)
            else:
                filtered_df[name] = round(filtered_df[existing_name]
                                          - filtered_df[f'{existing_name}_prev'], 2)

            # Fill NaN values in 'field_diff' with 'field' from the current DataFrame
            filtered_df[name].fillna(filtered_df[existing_name])

            # iterating through 'options' inside every field and applying them
            for filter_data in obj.get('options', {}):
                option = filter_data['option']
                value = filter_data['value']

                comparison_func = self.comparison_functions[option]

                # get comparison function in order to further filtration of DataFrame
                filter_condition = comparison_func(filtered_df[name], value)

                filtered_df = filtered_df[filter_condition]

        result_df = filtered_df[common_fields + exception_fields + dataframe_fields]
        return result_df

    def apply_nullable_diff(self, cut_dataframe: pd.DataFrame) -> pd.DataFrame:
        for obj in self.agg.dataframe_filtering:
            name: str = obj.get('name')
            existing_name = name.replace(DIFF, '').replace(PERCENT, '')

            cut_dataframe[name] = cut_dataframe[existing_name]

            for filter_data in obj.get('options', {}):
                option = filter_data['option']
                value = filter_data['value']

                comparison_func = self.comparison_functions[option]

                # get comparison function in order to further filtration of DataFrame
                filter_condition = comparison_func(cut_dataframe[name], value)

                cut_dataframe = cut_dataframe[filter_condition]

        return cut_dataframe

    def find_percent(self, curr_value: float, prev_value: float) -> float:
        difference = curr_value - prev_value
        try:
            return difference * 100 / prev_value
        except ZeroDivisionError:
            return difference

    def find_additions_metrics(self, current_range_response: list, prev_range_response: list) -> list:
        """
        Execute evaluation of metrics in dataframe
        """
        if not current_range_response:
            return []

        current_range_df = pd.DataFrame(current_range_response)
        prev_range_df = pd.DataFrame(prev_range_response)

        # set nullable DataFrame in case if further there will be need
        # to cut current daterange DataFrame
        cut_current_range_df: pd.DataFrame = pd.DataFrame()

        if self.agg.has_intervals:
            # getting timedelta of previous daterange and current daterange
            prev_timedelta = self.get_timedelta(list(self.agg.date_previous_pre_filtering.values())[0],
                                                list(self.agg.date_previous_pre_filtering.values())[1])
            curr_timedelta = self.get_timedelta(list(self.agg.date_pre_filtering.values())[0],
                                                list(self.agg.date_pre_filtering.values())[1])

            # if timedelta of previous daterange is less, we cut off from current daterange DataFrame all
            # records, whose interval date does not match previous (it means we persist here only last days,
            # that could be evaluated with dates of previous range)
            if prev_timedelta < curr_timedelta:
                interval_field: str = self.get_interval_field()

                last_date_current_range = datetime.datetime.strptime(list(self.agg.date_pre_filtering.values())[1],
                                                                     '%Y-%m-%d')

                start_date_current_range: datetime = last_date_current_range - \
                    timedelta(days=prev_timedelta.days)

                # get period for further truncating of the date
                to_period_form = self.get_interval_class().get_to_period_by_name(self.get_interval_field())

                # Convert start_date_current_range to UTC datetime if it's not already and truncate
                # it to predefined period
                start_date_current_range = pd.to_datetime(start_date_current_range)\
                    .to_period(to_period_form)\
                    .to_timestamp()\
                    .tz_localize('UTC')

                # DataFrame whose intervals does NOT match previous daterange
                cut_current_df = current_range_df[current_range_df[interval_field] < start_date_current_range]

                # filters current DataFrame with only matching interval date
                current_range_df = current_range_df[current_range_df[interval_field] >= start_date_current_range]

                cut_current_range_df = self.apply_nullable_diff(cut_current_df)

        # defines common field by which it must be merged
        exception_fields = list(self.agg.main_annotation.keys()) + list(self.agg.pre_annotation.keys())
        common_fields = [field for field in current_range_df.columns if field not in exception_fields]

        if common_fields:
            # if DataFrame for previous period is nullable, we apply nullable difference on current DataFrame
            if prev_range_df.empty:
                result_df = self.apply_nullable_diff(current_range_df)
            else:
                filtered_df: pd.DataFrame = current_range_df.merge(prev_range_df, on=common_fields,
                                                                   suffixes=('', '_prev'))
                result_df = self.apply_dataframe_with_common_fields(filtered_df, common_fields, exception_fields)
        else:
            result_df = self.apply_dataframe_without_common_fields(current_range_df, prev_range_df)

        # if there is cut DataFrame with unmatched dates we concatenate it ignoring indexes
        if not cut_current_range_df.empty:
            result_df = pd.concat([cut_current_range_df, result_df], ignore_index=True)

        return result_df.to_dict(orient='records')


class MainAggregator(BaseMainAggregator):
    dimension_aggregator_class = DimensionAggregator
    metric_aggregator_class = MetricAggregator
    date_range_aggregator_class = DateRangesAggregator
    dataframe_aggregator_class = DataFrameAggregator
    model_name = CartItem   # basing model queries will be made

    def __init__(self, dimensions: list, metrics: list, date_range: list, prev_date_range: list = None):
        super().__init__(dimensions, metrics, date_range, prev_date_range)

        self.dimension_aggregator = self.dimension_aggregator_class(self.dimensions, self)
        self.metric_aggregator = self.metric_aggregator_class(self.metrics_data, self.model_name, self)
        self.date_range_aggregator = self.date_range_aggregator_class(self.date_range, self.prev_date_range, self)

    def rename_columns(self, queryset: list) -> list:
        df = pd.DataFrame(queryset)
        df.rename(columns=self.parsing_fields, inplace=True)
        return df.to_dict(orient='records')

    def search(self, df: pd.DataFrame, field: str, value: str) -> pd.DataFrame:
        if field not in DimensionEnum.get_all_dimension_fields() or field not in df.columns:
            raise ValidationError(detail={'error': _('Введіть коректне поле для пошуку.')})

        if not value:
            return df

        return df[df[field].astype(str).str.contains(value, regex=False)]

    def count_metric_totals(self, df: pd.DataFrame) -> pd.Series:
        """
        Evaluates totals for each metric field and adds it to the end of DataFrame
        """

        if df.empty:
            return pd.Series()

        # get the intersection of columns from MetricNameEnum and DataFrame,
        # excluding column which are non-billable or should be processed in another way
        columns_to_sum = [
            column for column in list(set(MetricNameEnum.get_values()) & set(df.columns))
            if column not in NON_BILLABLE_COLUMNS + MIN_DATE_COLUMNS + MAX_DATE_COLUMNS
        ]

        # get the intersection of min and max columns
        columns_to_min = list(set(MIN_DATE_COLUMNS) & set(df.columns))
        columns_to_max = list(set(MAX_DATE_COLUMNS) & set(df.columns))

        for column in columns_to_min + columns_to_max:
            df[column] = pd.to_datetime(df[column], format='%Y-%m-%d')

        min_evals = df[columns_to_min].min().apply(lambda x: x.strftime('%Y-%m-%d'))
        max_evals = df[columns_to_max].max().apply(lambda x: x.strftime('%Y-%m-%d'))

        # Calculate the sum for selected columns
        sums = df[columns_to_sum].sum().round(2)

        # Create the totals row with sum values and '-' in other columns
        totals_row = pd.Series(['Totals'], index=[df.columns[0]])
        totals_row = pd.concat([totals_row, sums, min_evals, max_evals])

        # name first column with 'Totals'
        for i, column in enumerate(df.columns):
            if i == 0:
                continue  # Skip the first column
            if column in NON_BILLABLE_COLUMNS \
                    or column not in MetricNameEnum.get_values():
                totals_row[column] = '-'

        return totals_row

    def sort_by_dimension_name(self, df: pd.DataFrame, dimension_field: str) -> pd.DataFrame:
        """
        Sorts values in DataFrame by indicated dimension field name
        """
        name_field = dimension_field.replace('-', '')

        if df.empty:
            return df

        # checks whether dimension field name is valid
        if name_field not in MetricNameEnum.get_values() or name_field not in df.columns:
            raise ValidationError(detail={'ordering': _('Введіть коректний розріз для сортування.')})

        return df.sort_values(by=name_field, ascending=(not dimension_field.startswith('-')))
