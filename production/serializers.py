
from rest_framework import serializers
from .models import ProductionBatch


class ProductionBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionBatch
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")
