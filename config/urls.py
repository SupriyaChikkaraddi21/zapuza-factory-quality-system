
"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from workflow.views import (
    AdvanceBatchView,
    BatchActionView,
    InspectionApprovalView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/production/", include("production.urls")),
    path("api/quality/", include("inspections.urls")),
    path(
        "api/auth/login/",
        obtain_auth_token,
        name="api-login",
    ),
    path(
        "api/workflow/batches/<int:batch_id>/advance/",
        AdvanceBatchView.as_view(),
        name="advance-batch",
    ),
    path(
        "api/workflow/inspections/<int:inspection_id>/review/",
        InspectionApprovalView.as_view(),
        name="inspection-review",
    ),
    path(
        "api/workflow/batches/<int:batch_id>/<str:action>/",
        BatchActionView.as_view(),
        name="batch-action",
    ),
]
