from rest_framework.serializers import ModelSerializer

from .models import Shop, ShopGroup


class ShopGroupDisplaySerializer(ModelSerializer):
    class Meta:
        model = ShopGroup
        fields = ["id", "name"]


class ShopSerializer(ModelSerializer):
    group = ShopGroupDisplaySerializer()

    class Meta:
        model = Shop
        fields = "__all__"


class ShopGroupSerializer(ModelSerializer):
    parent = ShopGroupDisplaySerializer()

    class Meta:
        model = ShopGroup
        fields = "__all__"
