
from django.db import transaction
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from inspections.models import QualityInspection
from production.models import ProductionBatch
from workflow.services import (
    advance_batch,
    hold_batch,
    release_batch,
    reject_batch,
)
from workflow.models import AuditLog

class AdvanceBatchView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, batch_id):
        reason = request.data.get("reason", "")

        if not isinstance(reason, str):
            return Response(
                {"error": "Reason must be a string."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            batch = advance_batch(
                batch_id,
                actor=request.user,
                reason=reason,
            )
        except ProductionBatch.DoesNotExist:
            return Response(
                {"error": "Production batch not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "Production batch advanced successfully.",
                "batch_id": batch.id,
                "batch_number": batch.batch_number,
                "current_stage": batch.current_stage,
                "status": batch.status,
            },
            status=status.HTTP_200_OK,
        )


class InspectionApprovalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, inspection_id):
        user = request.user

        # Only Quality Supervisors or superusers may review inspections.
        is_supervisor = user.groups.filter(
            name="Quality Supervisors"
        ).exists()

        if not (is_supervisor or user.is_superuser):
            return Response(
                {
                    "error": (
                        "Only authorized quality supervisors "
                        "can review inspections."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        decision = request.data.get("decision")

        if decision not in ("APPROVED", "REJECTED"):
            return Response(
                {
                    "error": (
                        "Decision must be either APPROVED or REJECTED."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            inspection = QualityInspection.objects.get(
                pk=inspection_id
            )
        except QualityInspection.DoesNotExist:
            return Response(
                {"error": "Quality inspection not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if inspection.result == QualityInspection.Result.PENDING:
            return Response(
                {
                    "error": (
                        "Pending inspections cannot be approved or rejected "
                        "until a measurement is recorded."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            decision == "APPROVED"
            and inspection.result != QualityInspection.Result.PASS
        ):
            return Response(
                {
                    "error": (
                        "Only inspections with a PASS result can be approved."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            inspection.approval_status
            != QualityInspection.ApprovalStatus.PENDING_REVIEW
        ):
            return Response(
                {"error": "This inspection has already been reviewed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        previous_value = {
            "approval_status": inspection.approval_status,
            "approved_by": (
                inspection.approved_by.username
                if inspection.approved_by
                else None
            ),
        }

        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()
        else:
            ip_address = request.META.get("REMOTE_ADDR")

        device_serial = request.headers.get("X-Device-ID", "").strip()
        if len(device_serial) > 150:
            return Response(
                {
                    "error": (
                        "Device identifier must not exceed 150 characters."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # The inspection update and audit entry succeed or fail together.
        with transaction.atomic():
            inspection.approval_status = decision
            inspection.approved_by = user
            inspection.approved_at = timezone.now()
            inspection.save(
                update_fields=[
                    "approval_status",
                    "approved_by",
                    "approved_at",
                ]
            )

            AuditLog.objects.create(
                user=user,
                action=(
                    AuditLog.Action.INSPECTION_APPROVED
                    if decision == "APPROVED"
                    else AuditLog.Action.INSPECTION_REJECTED
                ),
                batch=inspection.batch,
                inspection=inspection,
                ip_address=ip_address or None,
                device_serial=device_serial,
                previous_value=previous_value,
                new_value={
                    "approval_status": inspection.approval_status,
                    "approved_by": user.username,
                    "approved_at": inspection.approved_at.isoformat(),
                },
                details=(
                    f"Inspection #{inspection.id} was {decision.lower()} "
                    f"by {user.username}."
                ),
            )

        return Response(
            {
                "message": "Inspection review recorded successfully.",
                "inspection_id": inspection.id,
                "batch_number": inspection.batch.batch_number,
                "result": inspection.result,
                "approval_status": inspection.approval_status,
                "approved_by": user.username,
                "approved_at": inspection.approved_at,
            },
            status=status.HTTP_200_OK,
        )

class BatchActionView(APIView):
    permission_classes = [IsAuthenticated]

    ACTIONS = {
        "hold": {
            "service": hold_batch,
            "message": "Production batch put on hold successfully.",
        },
        "release": {
            "service": release_batch,
            "message": "Production batch released successfully.",
        },
        "reject": {
            "service": reject_batch,
            "message": "Production batch rejected successfully.",
        },
    }

    def post(self, request, batch_id, action):
        user = request.user

        # Only Quality Supervisors or superusers may act on batches.
        is_supervisor = user.groups.filter(
            name="Quality Supervisors"
        ).exists()

        if not (is_supervisor or user.is_superuser):
            return Response(
                {
                    "error": (
                        "Only authorized quality supervisors "
                        "can perform batch actions."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        action_config = self.ACTIONS.get(action)

        if action_config is None:
            return Response(
                {"error": "Unsupported batch action."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = request.data.get("reason", "")

        if not isinstance(reason, str) or not reason.strip():
            return Response(
                {"error": "A non-empty reason is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()
        else:
            ip_address = request.META.get("REMOTE_ADDR")

        device_serial = request.headers.get("X-Device-ID", "").strip()

        if len(device_serial) > 150:
            return Response(
                {
                    "error": (
                        "Device identifier must not exceed 150 characters."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            batch = action_config["service"](
                batch_id,
                actor=user,
                reason=reason.strip(),
                ip_address=ip_address or None,
                device_serial=device_serial,
            )
        except ProductionBatch.DoesNotExist:
            return Response(
                {"error": "Production batch not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": action_config["message"],
                "batch_id": batch.id,
                "batch_number": batch.batch_number,
                "current_stage": batch.current_stage,
                "status": batch.status,
            },
            status=status.HTTP_200_OK,
        )
