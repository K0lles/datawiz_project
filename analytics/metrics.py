from django.db.models import Avg, Count, Sum
from django.utils.translation import gettext_lazy as _

from analytics.serializers import MetricOptionBaseModel


class ModelMetric:
    base_field = None   # Field which define way from current model to Receipt model
    base_model = MetricOptionBaseModel

    def __init__(self, name: str, option: dict = None):
        self.name = name
        self.option = option

        self.base_field: str = getattr(self, 'base_field', None)

        if not self.base_field:
            raise AttributeError(f'The field "base_field" is not defined in {self.__class__.__name__}.')

        self.select_related = []
        self.prefetch_related = []
        self.distinct_fields = []

    def process_options(self):
        validated_dict = self.base_model(**self.option).dict()
        return {f'{self.name}__{validated_dict.get("option", None)}': validated_dict.get('value')}

    def perform_field_assignment(self, field: str):
        """
        Performs concatenation of base model field 'base_field' to defined
        receipt's field.
        """
        self.prefetch_related.append(f'{self.base_field}__cartitem_set')
        return f'{self.cut_base_field()}__{field}'

    def cut_base_field(self):
        return self.base_field.replace('_set', '')

    def average_price(self) -> dict[str, Avg]:
        """
        Returns annotate query for getting average price of
        receipts
        """
        field_to_paste = self.perform_field_assignment('cartitem__price')
        query = {self.name: Avg(field_to_paste)}
        return query

    def turnover(self) -> dict[str, Sum]:
        """
        Returns annotate query for getting turnover
        by summing of qty sold items
        """
        field_to_paste = self.perform_field_assignment('cartitem__qty')
        query = {self.name: Sum(field_to_paste)}
        return query

    def income(self) -> dict[str, Sum]:
        """
        Returns annotate query for getting income
        """
        field_to_paste = self.perform_field_assignment('cartitem__margin_price_total')
        query = {self.name: Sum(field_to_paste)}
        return query

    def sold_product_amount(self) -> dict[str, Sum]:
        """
        Returns annotate query for getting sold amount of products
        """
        field_to_paste = self.perform_field_assignment('cartitem__qty')
        query = {self.name: Sum(field_to_paste)}
        return query

    def receipt_amount(self) -> dict[str, Count]:
        """
        Returns annotate query for getting amount of receipts
        """
        field_to_paste = self.perform_field_assignment('receipt')
        query = {self.name: Count(field_to_paste, distinct=True)}

        self.select_related.append(field_to_paste)
        self.prefetch_related = []

        return query

    def clear_related(self) -> None:
        """
        If call many times some function,
        'prefetch_related' and 'select_related' will
        be duplicated
        """
        self.prefetch_related.clear()
        self.select_related.clear()
        self.distinct_fields.clear()

    def get_annotation_query(self) -> dict:
        self.clear_related()
        func = getattr(self, self.name, None)

        if not func:
            raise ValueError(_('Вкажіть правильний "name".'))

        return func()

    def response(self) -> dict:
        return {
            'annotation': self.get_annotation_query(),
            'post_filtering': self.process_options(),
            'select_related': self.select_related,
            'prefetch_related': self.prefetch_related,
            'distinct_fields': self.distinct_fields
        }


class ShopMetric(ModelMetric):
    base_field = 'receipt_set'


class ShopGroupMetric(ModelMetric):
    base_field = 'shop_set__receipt_set'


class CategoryMetric(ModelMetric):
    base_field = 'product_set'
