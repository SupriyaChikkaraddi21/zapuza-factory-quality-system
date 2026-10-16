
from django.urls import path

from .views import ProductionBatchListCreateView


urlpatterns = [
    path(
        "batches/",
        ProductionBatchListCreateView.as_view(),
        name="production-batch-list-create",
    ),
]
