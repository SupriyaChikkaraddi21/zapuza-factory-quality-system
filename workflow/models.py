
from django.conf import settings
from django.db import models

from production.models import ProductionBatch
from inspections.models import QualityInspection


class StageTransition(models.Model):
    batch = models.ForeignKey(
        ProductionBatch,
        on_delete=models.PROTECT,
        related_name="stage_transitions",
    )
    from_stage = models.CharField(max_length=30)
    to_stage = models.CharField(max_length=30)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.batch.batch_number}: "
            f"{self.from_stage} -> {self.to_stage}"
        )


class AuditLogQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValueError(
            "Audit log records cannot be modified."
        )

    def delete(self):
        raise ValueError(
            "Audit log records cannot be deleted."
        )


class AuditLog(models.Model):
    class Action(models.TextChoices):
        INSPECTION_APPROVED = (
            "INSPECTION_APPROVED",
            "Inspection Approved",
        )
        INSPECTION_REJECTED = (
            "INSPECTION_REJECTED",
            "Inspection Rejected",
        )
        STAGE_ADVANCED = (
            "STAGE_ADVANCED",
            "Production Stage Advanced",
        )
        BATCH_HELD = (
            "BATCH_HELD",
            "Production Batch Put On Hold",
        )
        BATCH_RELEASED = (
            "BATCH_RELEASED",
            "Production Batch Released From Hold",
        )
        BATCH_REJECTED = (
            "BATCH_REJECTED",
            "Production Batch Rejected",
        )
    objects = AuditLogQuerySet.as_manager()

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="quality_audit_logs",
    )
    action = models.CharField(
        max_length=40,
        choices=Action.choices,
    )
    batch = models.ForeignKey(
        ProductionBatch,
        on_delete=models.PROTECT,
        related_name="audit_logs",
    )
    inspection = models.ForeignKey(
        QualityInspection,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )
    device_serial = models.CharField(
        max_length=150,
        blank=True,
    )
    previous_value = models.JSONField(
        null=True,
        blank=True,
    )
    new_value = models.JSONField(
        null=True,
        blank=True,
    )
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.action} - {self.batch.batch_number} "
            f"by {self.user}"
        )

    def save(self, *args, **kwargs):
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise ValueError(
                "Audit log records cannot be modified."
            )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError(
            "Audit log records cannot be deleted."
        )
