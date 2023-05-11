from django.db.models import (Avg, CharField, Count, DateField, FloatField,
                              IntegerField, OuterRef, Subquery, Sum, TextField,
                              Value)
from django.utils.translation import gettext_lazy as _

from analytics.serializers import MetricOptionBaseModel
from receipts.models import CartItem


class ModelMetric:
    base_field = None  # Field which define way from current model to Receipt model
    option_validation_base_model = MetricOptionBaseModel
    contains_receipt = True  # if 'base_field' contains 'receipt'

    def __init__(self, name: str, options: list[dict] = None):
        self.name = name
        self.options = options

        self.base_field: str = getattr(self, 'base_field', None)

        if self.base_field is None:
            raise AttributeError(f'The field "base_field" is not defined in {self.__class__.__name__}.')

        self.select_related = []
        self.prefetch_related = []
        self.distinct_fields = []

    def process_options(self) -> dict | None:
        if self.options:
            filtering_options = {}
            for option in self.options:
                validated_dict = self.option_validation_base_model(**option).dict()
                filtering_options.update({f'{self.name}__{validated_dict.get("option", None)}':
                                          validated_dict.get('value')})
            return filtering_options

    def perform_field_assignment(self, field: str) -> str:
        """
        Performs concatenation of base model field 'base_field' to defined
        receipt's field.
        """
        self.extend_prefetch_related(f'{self.base_field}__cartitem_set')
        return f'{self.cut_base_field()}__{field}'

    def extend_prefetch_related(self, value: str) -> None:
        if self.name == 'receipt_amount':

            # if 'base_field' contains 'receipt_set' it is not necessary to add 'receipt_set' so
            # we could only cut off '__cartitem_set' in order to set 'receipt_set' as last point
            if self.contains_receipt:
                self.prefetch_related.append(value.replace('__cartitem_set', ''))
                return

            # if there is no 'receipt_set' in base_field, we must add 'receipt_set' here
            # note, that remain 'cartitem_set' as it is the only way to get to receipts
            self.prefetch_related.append(f'{value}__receipt_set')
            return

        self.prefetch_related.append(value)

    def cut_base_field(self) -> str:
        return self.base_field.replace('_set', '')

    def average_price(self) -> dict[str, Avg]:
        """
        Returns annotate query for getting average price of
        receipts
        """
        field_to_paste = self.perform_field_assignment('cartitem__price')
        query = {self.name: Avg(field_to_paste, output_field=FloatField())}
        return query

    def turnover(self) -> dict[str, Sum]:
        """
        Returns annotate query for getting turnover
        by summing of qty sold items
        """
        field_to_paste = self.perform_field_assignment('cartitem__qty')
        query = {self.name: Sum(field_to_paste, output_field=FloatField())}
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
        query = {self.name: Sum(field_to_paste, output_field=FloatField())}
        return query

    def receipt_amount(self) -> dict[str, Count]:
        """
        Returns annotate query for getting amount of receipts
        """
        field_to_paste = self.perform_field_assignment('receipt' if not self.contains_receipt else '')

        # if field ends with '__' in case absence 'receipt' in 'base_field'
        # it cuts off 2 last underscores
        if field_to_paste.endswith('__'):
            field_to_paste = field_to_paste[:len(field_to_paste) - 2]

        query = {self.name: Count(field_to_paste, distinct=True, output_field=IntegerField())}

        return query

    def form_subquery_filtering(self) -> dict:
        """
        Returns field which will be used in subquery filtering
        """
        reversed_fields = self.base_field.replace('_set', '').split('__')[::-1]
        class_name = self.__class__.__name__.lower().replace('metric', '')

        # forming fields, which will appears in subquery filtering
        filtering_cart_items_field = '__'.join(reversed_fields) + class_name + '__pk'

        filtering_fields = {filtering_cart_items_field: OuterRef('pk')}

        return filtering_fields

    def first_product_date(self) -> dict:
        subquery = CartItem.objects.filter(**self.form_subquery_filtering()).order_by('date').values('date')[:1]
        annotation = {'first_product_date': Subquery(subquery, output_field=DateField())}
        return annotation

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
        """
        Tries to get function based on self.name. If no
        function got raises ValueError
        """
        self.clear_related()
        func = getattr(self, self.name, None)

        if not func:
            raise ValueError(_('Вкажіть правильний "name".'))

        return func()

    def last_product_date(self) -> dict:
        subquery = CartItem.objects.filter(**self.form_subquery_filtering()).order_by('-date').values('date')[:1]
        annotation = {'last_product_date': Subquery(subquery, output_field=DateField())}
        return annotation

    def empty_value(self) -> dict:
        return {self.name: Value('-', output_field=CharField())}

    def product_article(self) -> dict:
        """
        Article of product will be returned only in Shop model metric
        """
        return self.empty_value()

    def product_barcode(self) -> dict:
        """
        Barcode of product will be returned only in Shop model metric
        """
        return self.empty_value()

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

    def product_article(self) -> dict:
        return {self.name: Value('article', output_field=TextField())}

    def product_barcode(self) -> dict:
        return {self.name: Value('barcode', output_field=TextField())}


class FullShopGroupShopMaterializedViewMetric(ModelMetric):
    base_field = 'shop_set__receipt_set'


class FullCategoryProductMaterializedViewMetric(ModelMetric):
    base_field = 'product_set'
    contains_receipt = False


class TerminalMetric(ModelMetric):
    base_field = 'receipt_set'
