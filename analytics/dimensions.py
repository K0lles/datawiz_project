class DimensionFieldAssignment:
    way_from_cartitems: str = None   # Field which define way from CartItem model to current model (with '_set')
    use_select_related = False
    parsing_field_cut = 2

    def __init__(self, name: str, filtering: dict[str] = None, pre_values: list | None = None):
        if getattr(self, 'way_from_cartitems') is None:
            raise AttributeError(f'You need to define "way_to_cartitems" is {self.__class__.__name__}.')

        self.name: str = name
        self.filtering: dict = filtering if filtering else {}
        self.pre_values: list = pre_values if pre_values else []

        self.adapted_filtering: dict = {}
        self.adapted_pre_values: list[str] = []

        # self.select_related: list = [self.cut_way_field()] if self.use_select_related else []
        # self.prefetch_related = [self.way_from_cartitems] if not self.use_select_related else []
        self.select_related = []
        self.prefetch_related = []
        self.parsed_field_names = {}

    def cut_way_field(self) -> str:
        """
        Removes all '_set' from 'way_to_cartitems' field
        """
        return self.way_from_cartitems.replace('_set', '')

    def adapt_filtering(self) -> None:
        """
        Concatenate field for filtration with set 'way_from_cartitems' field
        """
        self.adapted_filtering = {}
        for key, value in self.filtering.items():
            self.adapted_filtering[f'{self.cut_way_field()}__{key}'] = value

    def adapt_pre_values(self) -> None:
        """
        Concatenate each item in pre_values with set 'way_from_cartitems' field
        """
        self.adapted_pre_values = []
        for value in self.pre_values:
            self.adapted_pre_values.append(f'{self.cut_way_field()}__{value}')

    def form_parsed_field_names(self) -> None:
        """
        Creates dict of values, where key is the current name
        and its value is the name field should be renamed to for
        display
        """
        for value in self.adapted_pre_values:
            split_field_name = value.split('__')
            parsed_field = f'{split_field_name[len(split_field_name) - self.parsing_field_cut]}' \
                           f'__{split_field_name[len(split_field_name) - 1]}'
            if parsed_field != value:
                self.parsed_field_names[value] = parsed_field

    def execute_all(self) -> None:
        """
        Run all necessary methods for response. Could be
        overwritten
        """
        self.adapt_filtering()
        self.adapt_pre_values()
        self.form_parsed_field_names()

    def response(self) -> dict:
        """
        Returns adapted data
        """
        self.execute_all()
        return {
            'pre_filtering': self.adapted_filtering,
            'pre_values': self.adapted_pre_values,
            'parsed_field_names': self.parsed_field_names,
            'select_related': self.select_related,
            'prefetch_related': self.prefetch_related
        }


class FullCategoryProductMaterializedViewFieldAssignment(DimensionFieldAssignment):
    way_from_cartitems = 'product__fullcategoryproductmaterializedview_set__category'


class ProductFieldAssignment(DimensionFieldAssignment):
    way_from_cartitems = 'product'
    use_select_related = True


class ProducerFieldAssignment(DimensionFieldAssignment):
    way_from_cartitems = 'product__producer'
    use_select_related = True


class SupplierFieldAssignment(DimensionFieldAssignment):
    way_from_cartitems = 'supplier'
    use_select_related = True


class TerminalFieldAssignment(DimensionFieldAssignment):
    way_from_cartitems = 'receipt_set__terminal_set'


class FullShopGroupShopMaterializedViewFieldAssignment(DimensionFieldAssignment):
    way_from_cartitems = 'receipt__shop__fullshopgroupshopmaterializedview_set__group'


class ShopFieldAssignment(DimensionFieldAssignment):
    way_from_cartitems = 'receipt__shop'
    use_select_related = True
