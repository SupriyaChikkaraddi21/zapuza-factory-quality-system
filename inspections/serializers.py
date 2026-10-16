from rest_framework import serializers

from .models import QualityInspection


class QualityInspectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityInspection
        fields = "__all__"
        read_only_fields = (
            "result",
            "approval_status",
            "approved_by",
            "approved_at",
            "inspected_at",
            "created_at",
        )

    def validate(self, attrs):
        lower_limit = attrs.get(
            "lower_limit",
            getattr(self.instance, "lower_limit", None),
        )
        upper_limit = attrs.get(
            "upper_limit",
            getattr(self.instance, "upper_limit", None),
        )

        if (
            lower_limit is not None
            and upper_limit is not None
            and lower_limit > upper_limit
        ):
            raise serializers.ValidationError({
                "lower_limit": (
                    "Lower limit cannot exceed upper limit."
                )
            })

        return attrs