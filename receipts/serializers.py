from rest_framework.serializers import ModelSerializer

from receipts.models import Supplier, Terminal
from shops.serializers import ShopSerializer


class SupplierSerializer(ModelSerializer):
    class Meta:
        model = Supplier
        fields = "__all__"


class TerminalSerializer(ModelSerializer):
    shop = ShopSerializer()

    class Meta:
        model = Terminal
        fields = "__all__"
