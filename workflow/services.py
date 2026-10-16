from django.db import transaction

from production.models import ProductionBatch
from inspections.models import QualityInspection
from workflow.models import AuditLog, StageTransition

STAGE_ORDER = [
    ProductionBatch.Stage.RAW_MATERIAL,
    ProductionBatch.Stage.MACHINING,
    ProductionBatch.Stage.HEAT_TREATMENT,
    ProductionBatch.Stage.GRINDING,
    ProductionBatch.Stage.FINAL_INSPECTION,
    ProductionBatch.Stage.PACKING,
    ProductionBatch.Stage.DISPATCHED,
]


@transaction.atomic
def advance_batch(batch_id, actor, reason=""):
    batch = ProductionBatch.objects.select_for_update().get(
        pk=batch_id
    )

    if batch.status != ProductionBatch.Status.IN_PROGRESS:
        raise ValueError("Only in-progress batches can advance.")

    current_stage = batch.current_stage

    if current_stage == ProductionBatch.Stage.DISPATCHED:
        raise ValueError("This batch has already been dispatched.")

    current_index = STAGE_ORDER.index(current_stage)
    next_stage = STAGE_ORDER[current_index + 1]

    # Require at least one inspection at the current stage.
    stage_inspections = QualityInspection.objects.filter(
        batch=batch,
        stage=current_stage,
    )

    if not stage_inspections.exists():
        raise ValueError(
            "Cannot advance because no inspection has been recorded "
            "for the current stage."
        )

    # Block advancement if any inspection has failed.
    failed_inspections = stage_inspections.filter(
        result=QualityInspection.Result.FAIL,
    ).exists()

    if failed_inspections:
        raise ValueError(
            "Cannot advance this batch because the current stage "
            "has failed inspections."
        )

    # Block advancement if any measurement is pending.
    pending_inspections = stage_inspections.filter(
        result=QualityInspection.Result.PENDING,
    ).exists()

    if pending_inspections:
        raise ValueError(
            "Cannot advance because the current stage has pending "
            "inspections."
        )

    # Require supervisor approval for every inspection.
    unapproved_inspections = stage_inspections.exclude(
        approval_status=QualityInspection.ApprovalStatus.APPROVED
    ).exists()

    if unapproved_inspections:
        raise ValueError(
            "Cannot advance because current-stage inspections "
            "have not all been approved by a supervisor."
        )

    # Final inspection requires at least one passing inspection.
    if current_stage == ProductionBatch.Stage.FINAL_INSPECTION:
        passed_inspections = stage_inspections.filter(
            result=QualityInspection.Result.PASS,
        ).exists()

        if not passed_inspections:
            raise ValueError(
                "At least one passed final inspection is required."
            )

    # Record the successful stage transition.
    StageTransition.objects.create(
        batch=batch,
        from_stage=current_stage,
        to_stage=next_stage,
        reason=reason,
    )

    # Record the stage advancement in the audit log.
    AuditLog.objects.create(
        user=actor,
        action=AuditLog.Action.STAGE_ADVANCED,
        batch=batch,
        previous_value={
            "current_stage": current_stage,
            "status": batch.status,
        },
        new_value={
            "current_stage": next_stage,
            "status": (
                ProductionBatch.Status.COMPLETED
                if next_stage == ProductionBatch.Stage.DISPATCHED
                else batch.status
            ),
        },
        details=(
            f"Batch {batch.batch_number} advanced "
            f"from {current_stage} to {next_stage}."
        ),
    )
    batch.current_stage = next_stage

    if next_stage == ProductionBatch.Stage.DISPATCHED:
        batch.status = ProductionBatch.Status.COMPLETED

    batch.save(
        update_fields=["current_stage", "status", "updated_at"]
    )

    return batch

@transaction.atomic
def hold_batch(
    batch_id,
    actor,
    reason="",
    ip_address=None,
    device_serial="",
):
    batch = ProductionBatch.objects.select_for_update().get(
        pk=batch_id
    )

    if batch.status != ProductionBatch.Status.IN_PROGRESS:
        raise ValueError(
            "Only in-progress batches can be put on hold."
        )

    if not reason.strip():
        raise ValueError("A reason is required to put a batch on hold.")

    previous_status = batch.status
    batch.status = ProductionBatch.Status.ON_HOLD
    batch.save(update_fields=["status", "updated_at"])

    AuditLog.objects.create(
        user=actor,
        action=AuditLog.Action.BATCH_HELD,
        batch=batch,
        ip_address=ip_address or None,
        device_serial=device_serial,
        previous_value={"status": previous_status},
        new_value={"status": batch.status},
        details=(
            f"Batch {batch.batch_number} put on hold by "
            f"{actor.username}. Reason: {reason.strip()}"
        ),
    )

    return batch


@transaction.atomic
def release_batch(
    batch_id,
    actor,
    reason="",
    ip_address=None,
    device_serial="",
):
    batch = ProductionBatch.objects.select_for_update().get(
        pk=batch_id
    )

    if batch.status != ProductionBatch.Status.ON_HOLD:
        raise ValueError("Only batches on hold can be released.")

    if not reason.strip():
        raise ValueError("A reason is required to release a batch.")

    previous_status = batch.status
    batch.status = ProductionBatch.Status.IN_PROGRESS
    batch.save(update_fields=["status", "updated_at"])

    AuditLog.objects.create(
        user=actor,
        action=AuditLog.Action.BATCH_RELEASED,
        batch=batch,
        ip_address=ip_address or None,
        device_serial=device_serial,
        previous_value={"status": previous_status},
        new_value={"status": batch.status},
        details=(
            f"Batch {batch.batch_number} released from hold by "
            f"{actor.username}. Reason: {reason.strip()}"
        ),
    )

    return batch


@transaction.atomic
def reject_batch(
    batch_id,
    actor,
    reason="",
    ip_address=None,
    device_serial="",
):
    batch = ProductionBatch.objects.select_for_update().get(
        pk=batch_id
    )

    if batch.status != ProductionBatch.Status.IN_PROGRESS:
        raise ValueError(
            "Only in-progress batches can be rejected."
        )

    if not reason.strip():
        raise ValueError("A reason is required to reject a batch.")

    previous_status = batch.status
    batch.status = ProductionBatch.Status.REJECTED
    batch.save(update_fields=["status", "updated_at"])

    AuditLog.objects.create(
        user=actor,
        action=AuditLog.Action.BATCH_REJECTED,
        batch=batch,
        ip_address=ip_address or None,
        device_serial=device_serial,
        previous_value={"status": previous_status},
        new_value={"status": batch.status},
        details=(
            f"Batch {batch.batch_number} rejected by "
            f"{actor.username}. Reason: {reason.strip()}"
        ),
    )

    return batch
