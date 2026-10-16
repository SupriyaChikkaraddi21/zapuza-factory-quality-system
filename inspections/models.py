from django.db import models
from django.utils import timezone

from production.models import ProductionBatch


class QualityInspection(models.Model):
    class Result(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PASS = "PASS", "Pass"
        FAIL = "FAIL", "Fail"

    class ApprovalStatus(models.TextChoices):
        PENDING_REVIEW = "PENDING_REVIEW", "Pending Review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    batch = models.ForeignKey(
        ProductionBatch,
        on_delete=models.PROTECT,
        related_name="inspections",
    )

    stage = models.CharField(
        max_length=30,
        choices=ProductionBatch.Stage.choices,
        default=ProductionBatch.Stage.RAW_MATERIAL,
    )

    parameter_name = models.CharField(max_length=100)

    nominal_value = models.DecimalField(
        max_digits=10,
        decimal_places=3,
    )

    lower_limit = models.DecimalField(
        max_digits=10,
        decimal_places=3,
    )

    upper_limit = models.DecimalField(
        max_digits=10,
        decimal_places=3,
    )

    measured_value = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
    )

    result = models.CharField(
        max_length=10,
        choices=Result.choices,
        default=Result.PENDING,
    )

    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING_REVIEW,
    )

    approved_by = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="quality_inspections_reviewed",
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    inspector_remarks = models.TextField(blank=True)

    inspected_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def evaluate_measurement(self):
        if self.lower_limit > self.upper_limit:
            raise ValueError(
                "Lower limit cannot exceed upper limit."
            )

        if self.measured_value is None:
            self.result = self.Result.PENDING

        elif (
            self.lower_limit
            <= self.measured_value
            <= self.upper_limit
        ):
            self.result = self.Result.PASS

        else:
            self.result = self.Result.FAIL

        return self.result

    def save(self, *args, **kwargs):
        self.evaluate_measurement()

        if (
            self.measured_value is not None
            and self.inspected_at is None
        ):
            self.inspected_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.batch.batch_number} - "
            f"{self.parameter_name}"
        )