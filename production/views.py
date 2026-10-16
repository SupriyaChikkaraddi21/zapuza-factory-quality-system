
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import ProductionBatch
from .serializers import ProductionBatchSerializer


class ProductionBatchListCreateView(generics.ListCreateAPIView):
    queryset = ProductionBatch.objects.all().order_by("-created_at")
    serializer_class = ProductionBatchSerializer
    permission_classes = [IsAuthenticated]
