
from django.contrib import admin
from .models import QualityInspection


@admin.register(QualityInspection)
class QualityInspectionAdmin(admin.ModelAdmin):
    readonly_fields = ("result",)

    list_display = (
        "batch",
        "parameter_name",
        "nominal_value",
        "measured_value",
        "result",
        "created_at",
    )

    list_filter = ("result",)

    search_fields = (
        "batch__batch_number",
        "parameter_name",
    )
