
from django.contrib import admin
from .models import StageTransition


@admin.register(StageTransition)
class StageTransitionAdmin(admin.ModelAdmin):
    list_display = (
        "batch",
        "from_stage",
        "to_stage",
        "created_at",
    )
    list_filter = ("from_stage", "to_stage")
    search_fields = ("batch__batch_number", "reason")
    readonly_fields = ("created_at",)
