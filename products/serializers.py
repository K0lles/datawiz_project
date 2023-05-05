from rest_framework.serializers import ModelSerializer

from .models import Category, Producer, Product


class CategoryDisplaySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class CategorySerializer(ModelSerializer):
    parent = CategoryDisplaySerializer()

    class Meta:
        model = Category
        fields = "__all__"


class ProducerSerializer(ModelSerializer):
    class Meta:
        model = Producer
        fields = "__all__"


class ProductSerializer(ModelSerializer):
    category = CategoryDisplaySerializer()
    producer = ProducerSerializer()

    class Meta:
        model = Product
        fields = "__all__"
