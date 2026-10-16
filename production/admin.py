
from django.contrib import admin
from .models import ProductionBatch


@admin.register(ProductionBatch)
class ProductionBatchAdmin(admin.ModelAdmin):
    list_display = (
        "batch_number",
        "part_number",
        "quantity",
        "current_stage",
        "status",
        "created_at",
    )
    list_filter = ("current_stage", "status")
    search_fields = ("batch_number", "part_number")
