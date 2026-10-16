
from django.db import models


class ProductionBatch(models.Model):
    class Stage(models.TextChoices):
        RAW_MATERIAL = "RAW_MATERIAL", "Raw Material"
        MACHINING = "MACHINING", "Machining"
        HEAT_TREATMENT = "HEAT_TREATMENT", "Heat Treatment"
        GRINDING = "GRINDING", "Grinding"
        FINAL_INSPECTION = "FINAL_INSPECTION", "Final Inspection"
        PACKING = "PACKING", "Packing"
        DISPATCHED = "DISPATCHED", "Dispatched"

    class Status(models.TextChoices):
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        ON_HOLD = "ON_HOLD", "On Hold"
        REJECTED = "REJECTED", "Rejected"
        COMPLETED = "COMPLETED", "Completed"

    batch_number = models.CharField(max_length=30, unique=True)
    part_number = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField()
    current_stage = models.CharField(
        max_length=30,
        choices=Stage.choices,
        default=Stage.RAW_MATERIAL,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.batch_number
