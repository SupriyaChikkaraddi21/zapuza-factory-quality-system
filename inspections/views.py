
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import QualityInspection
from .serializers import QualityInspectionSerializer


class QualityInspectionListCreateView(generics.ListCreateAPIView):
    queryset = QualityInspection.objects.all().order_by("-created_at")
    serializer_class = QualityInspectionSerializer
    permission_classes = [IsAuthenticated]


class QualityInspectionMeasurementView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, inspection_id):
        try:
            inspection = QualityInspection.objects.get(
                pk=inspection_id
            )
        except QualityInspection.DoesNotExist:
            return Response(
                {"error": "Inspection not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if inspection.measured_value is not None:
            return Response(
                {
                    "error": (
                        "A measurement has already been recorded. "
                        "Measurements cannot be overwritten."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_value = request.data.get("measured_value")

        if raw_value is None or isinstance(raw_value, bool):
            return Response(
                {"error": "A numeric measured_value is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            measured_value = Decimal(str(raw_value))
        except (InvalidOperation, ValueError, TypeError):
            return Response(
                {"error": "Enter a valid numeric measurement."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not measured_value.is_finite():
            return Response(
                {"error": "Measurement must be a finite number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if measured_value.as_tuple().exponent < -3:
            return Response(
                {
                    "error": (
                        "Measurement can have at most "
                        "3 decimal places."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if measured_value.copy_abs() >= Decimal("10000000"):
            return Response(
                {"error": "Measurement is outside the supported range."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        remarks = request.data.get("inspector_remarks", "")

        if not isinstance(remarks, str):
            return Response(
                {"error": "Inspector remarks must be text."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        inspection.measured_value = measured_value
        inspection.inspector_remarks = remarks.strip()
        inspection.inspected_at = timezone.now()
        inspection.evaluate_measurement()
        inspection.save()

        return Response(
            {
                "message": "Measurement recorded successfully.",
                "inspection": QualityInspectionSerializer(
                    inspection
                ).data,
            },
            status=status.HTTP_200_OK,
        )
