
from django.urls import path

from .views import (
    QualityInspectionListCreateView,
    QualityInspectionMeasurementView,
)


urlpatterns = [
    path(
        "inspections/",
        QualityInspectionListCreateView.as_view(),
        name="inspection-list-create",
    ),
    path(
        "inspections/<int:inspection_id>/measurement/",
        QualityInspectionMeasurementView.as_view(),
        name="inspection-record-measurement",
    ),
]
