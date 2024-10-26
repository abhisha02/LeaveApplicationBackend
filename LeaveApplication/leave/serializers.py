from rest_framework import serializers
from .models import LeaveRequest
from api.models import Employee


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            "id",
            "employee",
            "employee_name",
            "leave_type",
            "start_date",
            "end_date",
            "reason",
            "status",
            "submission_date",
        ]

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"

    def validate(self, data):
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        # Check if start_date or end_date are empty strings
        if start_date == "":
            raise serializers.ValidationError({"start_date": "Start date is required."})
        if end_date == "":
            raise serializers.ValidationError({"end_date": "End date is required."})

        # Ensure both dates are provided and not empty
        if start_date is None:
            raise serializers.ValidationError({"start_date": "Start date is required."})

        if end_date is None:
            raise serializers.ValidationError({"end_date": "End date is required."})

        # Ensure that start_date is before or the same as end_date
        if start_date > end_date:
            raise serializers.ValidationError(
                {"end_date": "End date cannot be before start date."}
            )

        # Here you can convert dates to the appropriate format if needed

        return data