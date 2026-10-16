from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from rest_framework.test import APIClient
from inspections.models import QualityInspection
from production.models import ProductionBatch
from workflow.models import AuditLog, StageTransition
from workflow.services import (
    advance_batch,
    hold_batch,
    release_batch,
    reject_batch,
)


User = get_user_model()


class WorkflowAdvanceBatchTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="workflow_test_user",
            password="test-password-123",
        )

        self.batch = ProductionBatch.objects.create(
            batch_number="TEST-WORKFLOW-001",
            part_number="TEST-PART-001",
            quantity=1,
            current_stage=ProductionBatch.Stage.RAW_MATERIAL,
            status=ProductionBatch.Status.IN_PROGRESS,
        )

    def assert_batch_did_not_advance(self):
        self.batch.refresh_from_db()

        self.assertEqual(
            self.batch.current_stage,
            ProductionBatch.Stage.RAW_MATERIAL,
        )

        self.assertFalse(
            AuditLog.objects.filter(
                batch=self.batch,
                action=AuditLog.Action.STAGE_ADVANCED,
            ).exists()
        )

    def test_batch_cannot_advance_without_inspections(self):
        expected_error = (
            "Cannot advance because no inspection has been recorded "
            "for the current stage."
        )

        with self.assertRaisesMessage(ValueError, expected_error):
            advance_batch(
                self.batch.id,
                actor=self.user,
                reason="Automated test",
            )

        self.assert_batch_did_not_advance()

    def test_batch_cannot_advance_with_failed_inspection(self):
        QualityInspection.objects.create(
            batch=self.batch,
            stage=ProductionBatch.Stage.RAW_MATERIAL,
            parameter_name="Test shaft diameter",
            nominal_value="25.000",
            lower_limit="24.900",
            upper_limit="25.100",
            measured_value="25.200",
            approval_status=QualityInspection.ApprovalStatus.APPROVED,
        )

        expected_error = (
            "Cannot advance this batch because the current stage "
            "has failed inspections."
        )

        with self.assertRaisesMessage(ValueError, expected_error):
            advance_batch(
                self.batch.id,
                actor=self.user,
                reason="Automated failed-inspection test",
            )

        self.assert_batch_did_not_advance()

    def test_batch_cannot_advance_with_pending_inspection(self):
        QualityInspection.objects.create(
            batch=self.batch,
            stage=ProductionBatch.Stage.RAW_MATERIAL,
            parameter_name="Pending test diameter",
            nominal_value="25.000",
            lower_limit="24.900",
            upper_limit="25.100",
            measured_value=None,
        )

        expected_error = (
            "Cannot advance because the current stage has pending "
            "inspections."
        )

        with self.assertRaisesMessage(ValueError, expected_error):
            advance_batch(
                self.batch.id,
                actor=self.user,
                reason="Automated pending-inspection test",
            )

        self.assert_batch_did_not_advance()

    def test_batch_cannot_advance_without_supervisor_approval(self):
        QualityInspection.objects.create(
            batch=self.batch,
            stage=ProductionBatch.Stage.RAW_MATERIAL,
            parameter_name="Unapproved test diameter",
            nominal_value="25.000",
            lower_limit="24.900",
            upper_limit="25.100",
            measured_value="25.000",
            approval_status=QualityInspection.ApprovalStatus.PENDING_REVIEW,
        )

        expected_error = (
            "Cannot advance because current-stage inspections "
            "have not all been approved by a supervisor."
        )

        with self.assertRaisesMessage(ValueError, expected_error):
            advance_batch(
                self.batch.id,
                actor=self.user,
                reason="Automated approval-requirement test",
            )

        self.assert_batch_did_not_advance()

    def test_batch_advances_with_approved_passing_inspection(self):
        QualityInspection.objects.create(
            batch=self.batch,
            stage=ProductionBatch.Stage.RAW_MATERIAL,
            parameter_name="Approved test diameter",
            nominal_value="25.000",
            lower_limit="24.900",
            upper_limit="25.100",
            measured_value="25.000",
            approval_status=QualityInspection.ApprovalStatus.APPROVED,
            approved_by=self.user,
        )

        batch = advance_batch(
            self.batch.id,
            actor=self.user,
            reason="Automated successful advancement test",
        )

        self.batch.refresh_from_db()

        self.assertEqual(
            batch.current_stage,
            ProductionBatch.Stage.MACHINING,
        )
        self.assertEqual(
            self.batch.current_stage,
            ProductionBatch.Stage.MACHINING,
        )
        self.assertEqual(
            self.batch.status,
            ProductionBatch.Status.IN_PROGRESS,
        )

        self.assertTrue(
            StageTransition.objects.filter(
                batch=self.batch,
                from_stage=ProductionBatch.Stage.RAW_MATERIAL,
                to_stage=ProductionBatch.Stage.MACHINING,
            ).exists()
        )

        self.assertTrue(
            AuditLog.objects.filter(
                batch=self.batch,
                action=AuditLog.Action.STAGE_ADVANCED,
                user=self.user,
            ).exists()
        )

    def test_final_inspection_requires_a_passing_inspection(self):
        self.batch.current_stage = ProductionBatch.Stage.FINAL_INSPECTION
        self.batch.save(update_fields=["current_stage"])

        QualityInspection.objects.create(
            batch=self.batch,
            stage=ProductionBatch.Stage.FINAL_INSPECTION,
            parameter_name="Final visual inspection",
            nominal_value="25.000",
            lower_limit="24.900",
            upper_limit="25.100",
            measured_value="25.000",
            approval_status=QualityInspection.ApprovalStatus.APPROVED,
            approved_by=self.user,
        )

        QualityInspection.objects.create(
            batch=self.batch,
            stage=ProductionBatch.Stage.FINAL_INSPECTION,
            parameter_name="Final verification check",
            nominal_value="25.000",
            lower_limit="24.900",
            upper_limit="25.100",
            measured_value="25.200",
            approval_status=QualityInspection.ApprovalStatus.APPROVED,
            approved_by=self.user,
        )

        expected_error = (
            "Cannot advance this batch because the current stage "
            "has failed inspections."
        )

        with self.assertRaisesMessage(ValueError, expected_error):
            advance_batch(
                self.batch.id,
                actor=self.user,
                reason="Automated final-inspection test",
            )

        self.batch.refresh_from_db()

        self.assertEqual(
            self.batch.current_stage,
            ProductionBatch.Stage.FINAL_INSPECTION,
        )

        self.assertFalse(
            StageTransition.objects.filter(
                batch=self.batch,
                from_stage=ProductionBatch.Stage.FINAL_INSPECTION,
            ).exists()
        )

        self.assertFalse(
            AuditLog.objects.filter(
                batch=self.batch,
                action=AuditLog.Action.STAGE_ADVANCED,
            ).exists()
        )


class BatchStatusServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="batch_action_test_user",
            password="test-password-123",
        )

        self.batch = ProductionBatch.objects.create(
            batch_number="TEST-BATCH-ACTION-001",
            part_number="TEST-PART-ACTION-001",
            quantity=1,
            current_stage=ProductionBatch.Stage.RAW_MATERIAL,
            status=ProductionBatch.Status.IN_PROGRESS,
        )

    def test_hold_batch_records_status_and_audit_metadata(self):
        batch = hold_batch(
            self.batch.id,
            actor=self.user,
            reason="Quality investigation",
            ip_address="127.0.0.1",
            device_serial="test-device-001",
        )

        self.assertEqual(
            batch.status,
            ProductionBatch.Status.ON_HOLD,
        )

        log = AuditLog.objects.get(
            batch=batch,
            action=AuditLog.Action.BATCH_HELD,
        )

        self.assertEqual(
            log.previous_value,
            {"status": ProductionBatch.Status.IN_PROGRESS},
        )
        self.assertEqual(
            log.new_value,
            {"status": ProductionBatch.Status.ON_HOLD},
        )
        self.assertEqual(log.ip_address, "127.0.0.1")
        self.assertEqual(log.device_serial, "test-device-001")
        self.assertIn("Quality investigation", log.details)

    def test_release_batch_records_status_and_audit_metadata(self):
        hold_batch(
            self.batch.id,
            actor=self.user,
            reason="Initial hold",
        )

        batch = release_batch(
            self.batch.id,
            actor=self.user,
            reason="Investigation completed",
            ip_address="127.0.0.1",
            device_serial="test-device-002",
        )

        self.assertEqual(
            batch.status,
            ProductionBatch.Status.IN_PROGRESS,
        )

        log = AuditLog.objects.get(
            batch=batch,
            action=AuditLog.Action.BATCH_RELEASED,
        )

        self.assertEqual(
            log.previous_value,
            {"status": ProductionBatch.Status.ON_HOLD},
        )
        self.assertEqual(
            log.new_value,
            {"status": ProductionBatch.Status.IN_PROGRESS},
        )
        self.assertEqual(log.ip_address, "127.0.0.1")
        self.assertEqual(log.device_serial, "test-device-002")

    def test_reject_batch_records_status_and_audit_metadata(self):
        batch = reject_batch(
            self.batch.id,
            actor=self.user,
            reason="Critical quality defect",
            ip_address="127.0.0.1",
            device_serial="test-device-003",
        )

        self.assertEqual(
            batch.status,
            ProductionBatch.Status.REJECTED,
        )

        log = AuditLog.objects.get(
            batch=batch,
            action=AuditLog.Action.BATCH_REJECTED,
        )

        self.assertEqual(
            log.previous_value,
            {"status": ProductionBatch.Status.IN_PROGRESS},
        )
        self.assertEqual(
            log.new_value,
            {"status": ProductionBatch.Status.REJECTED},
        )
        self.assertEqual(log.ip_address, "127.0.0.1")
        self.assertEqual(log.device_serial, "test-device-003")
        self.assertIn("Critical quality defect", log.details)

    def test_hold_requires_a_reason(self):
        with self.assertRaisesMessage(ValueError, "A reason is required"):
            hold_batch(
                self.batch.id,
                actor=self.user,
                reason="   ",
            )

        self.batch.refresh_from_db()

        self.assertEqual(
            self.batch.status,
            ProductionBatch.Status.IN_PROGRESS,
        )
        self.assertFalse(
            AuditLog.objects.filter(batch=self.batch).exists()
        )

    def test_release_requires_batch_to_be_on_hold(self):
        with self.assertRaisesMessage(
            ValueError,
            "Only batches on hold can be released.",
        ):
            release_batch(
                self.batch.id,
                actor=self.user,
                reason="Invalid release",
            )

        self.assertFalse(
            AuditLog.objects.filter(
                batch=self.batch,
                action=AuditLog.Action.BATCH_RELEASED,
            ).exists()
        )

    def test_rejected_batch_cannot_be_advanced(self):
        reject_batch(
            self.batch.id,
            actor=self.user,
            reason="Rejected for testing",
        )

        with self.assertRaisesMessage(
            ValueError,
            "Only in-progress batches can advance.",
        ):
            advance_batch(
                self.batch.id,
                actor=self.user,
                reason="Must not advance",
            )

        self.batch.refresh_from_db()

        self.assertEqual(
            self.batch.status,
            ProductionBatch.Status.REJECTED,
        )

        self.assertFalse(
            StageTransition.objects.filter(
                batch=self.batch,
            ).exists()
        )

    def test_rejected_batch_cannot_be_rejected_twice(self):
        reject_batch(
            self.batch.id,
            actor=self.user,
            reason="First rejection",
        )

        with self.assertRaisesMessage(
            ValueError,
            "Only in-progress batches can be rejected.",
        ):
            reject_batch(
                self.batch.id,
                actor=self.user,
                reason="Duplicate rejection",
            )

        self.assertEqual(
            AuditLog.objects.filter(
                batch=self.batch,
                action=AuditLog.Action.BATCH_REJECTED,
            ).count(),
            1,
        )

class BatchActionAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.operator = User.objects.create_user(
            username="batch_api_operator",
            password="test-password-123",
        )

        self.supervisor = User.objects.create_user(
            username="batch_api_supervisor",
            password="test-password-123",
        )

        self.supervisor_group, _ = Group.objects.get_or_create(
            name="Quality Supervisors"
        )
        self.supervisor.groups.add(self.supervisor_group)

        self.batch = ProductionBatch.objects.create(
            batch_number="TEST-BATCH-API-001",
            part_number="TEST-PART-API-001",
            quantity=1,
            current_stage=ProductionBatch.Stage.RAW_MATERIAL,
            status=ProductionBatch.Status.IN_PROGRESS,
        )

        self.hold_url = (
            f"/api/workflow/batches/{self.batch.id}/hold/"
        )

    def test_unauthorized_operator_cannot_hold_batch(self):
        self.client.force_authenticate(user=self.operator)

        response = self.client.post(
            self.hold_url,
            {"reason": "Testing unauthorized access"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        self.batch.refresh_from_db()
        self.assertEqual(
            self.batch.status,
            ProductionBatch.Status.IN_PROGRESS,
        )

        self.assertFalse(
            AuditLog.objects.filter(batch=self.batch).exists()
        )

    def test_supervisor_can_hold_batch(self):
        self.client.force_authenticate(user=self.supervisor)

        response = self.client.post(
            self.hold_url,
            {"reason": "Supervisor quality investigation"},
            format="json",
            HTTP_X_DEVICE_ID="api-test-device",
        )
        self.assertEqual(response.status_code, 200)

        self.batch.refresh_from_db()
        self.assertEqual(
            self.batch.status,
            ProductionBatch.Status.ON_HOLD,
        )

        log = AuditLog.objects.get(
            batch=self.batch,
            action=AuditLog.Action.BATCH_HELD,
        )

        self.assertEqual(log.user, self.supervisor)
        self.assertEqual(log.device_serial, "api-test-device")
        self.assertIn(
            "Supervisor quality investigation",
            log.details,
        )

    def test_supervisor_cannot_hold_batch_without_reason(self):
        self.client.force_authenticate(user=self.supervisor)

        response = self.client.post(
            self.hold_url,
            {"reason": "   "},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        self.batch.refresh_from_db()
        self.assertEqual(
            self.batch.status,
            ProductionBatch.Status.IN_PROGRESS,
        )

        self.assertFalse(
            AuditLog.objects.filter(batch=self.batch).exists()
        )
