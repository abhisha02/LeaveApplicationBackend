from rest_framework import serializers
from .models import LeaveRequest
from api.models import Employee
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum
from .models import Holiday


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField(read_only=True)
    working_days = serializers.IntegerField(read_only=True)

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
            "working_days",
        ]

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"

    def calculate_working_days(self, start_date, end_date):
        working_days = 0
        current_date = start_date
        
        while current_date <= end_date:
            # Check if it's not a weekend (where Monday is 0 and Sunday is 6)
            if current_date.weekday() < 5:
                # Check if it's not a holiday
                is_holiday = Holiday.objects.filter(date=current_date).exists()
                if not is_holiday:
                    working_days += 1
            current_date += timedelta(days=1)
            
        return working_days

    def get_used_leaves(self, employee, leave_type, year):
        return LeaveRequest.objects.filter(
            employee=employee,
            leave_type=leave_type,
            start_date__year=year,
            status__in=['approved', 'pending']
        ).aggregate(total_days=Sum('working_days'))['total_days'] or 0

    def validate(self, data):
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        leave_type = data.get("leave_type")
        employee = data.get("employee")

        # Check if start_date or end_date are empty strings or None
        if not start_date:
            raise serializers.ValidationError({"start_date": "Start date is required."})
        if not end_date:
            raise serializers.ValidationError({"end_date": "End date is required."})

        # Ensure that start_date is before or the same as end_date
        if start_date > end_date:
            raise serializers.ValidationError(
                {"end_date": "End date cannot be before start date."}
            )

        # Calculate working days
        working_days = self.calculate_working_days(start_date, end_date)
        
        # Ensure there are working days in the selected period
        if working_days == 0:
            raise serializers.ValidationError(
                {"message": "Selected period contains no working days."}
            )

        # Define leave limits
        LEAVE_LIMITS = {
            'casual': 10,
            'maternity': 90,
            'sick': 6,
            'annual': 20
        }

        # Get already used leaves for this year
        current_year = timezone.now().year
        used_leaves = self.get_used_leaves(employee, leave_type, current_year)
        leave_limit = LEAVE_LIMITS.get(leave_type)
        
        # Calculate if the request would exceed the limit
        if used_leaves + working_days > leave_limit:
            remaining = max(0, leave_limit - used_leaves)
            raise serializers.ValidationError({
                "message": f"Leave limit exceeded for {leave_type} leave. "
                          f"You have used {used_leaves} days out of {leave_limit}. "
                          f"Only {remaining} days remaining."
            })

        # Add working_days to the validated data
        data['working_days'] = working_days
        
        return data
class LeaveTypeSerializer(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()
    max_days = serializers.IntegerField()