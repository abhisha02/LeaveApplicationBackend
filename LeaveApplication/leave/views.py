from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from .models import LeaveRequest
from .serializers import LeaveRequestSerializer,LeaveTypeSerializer
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.http import JsonResponse
from django.views import View
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView


class ApplyLeaveRequestView(generics.CreateAPIView):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data.copy()
        data["employee"] = user.id

        # Check for overlapping leave requests
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        
        if not start_date or not end_date:
            return Response(
                {"message": "Both start date and end date are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        overlapping_requests = LeaveRequest.objects.filter(
            employee=user,
            status__in=["pending", "approved"],
            start_date__lt=end_date,
            end_date__gte=start_date,
        )

        if overlapping_requests.exists():
            return Response(
                {"message": "A leave request already exists for the selected dates."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Use the serializer to validate and create the leave request
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        # Create the leave request
        self.perform_create(serializer)

        return Response(
            {
                "message": "Leave request submitted successfully.",
                "leave_request": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )
class LeaveTypesView(APIView):
    def get(self, request):
        # Get leave types with their details
        leave_types = [
            {
                "value": choice[0],
                "label": choice[1],
                "max_days": self.get_max_days(choice[0])
            }
            for choice in LeaveRequest.LEAVE_TYPE_CHOICES
        ]
        return Response(leave_types)
    
    def get_max_days(self, leave_type):
        # Define maximum days for each leave type
        max_days_map = {
            "annual": 20,
            "sick": 6,
            "casual": 10,
            "maternity": 90
        }
        return max_days_map.get(leave_type, 0)


# API view to list the leave history for the current user (employee)
class LeaveHistoryView(generics.ListAPIView):
    queryset = LeaveRequest.objects.all().order_by('-submission_date') 
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]

    # Override the queryset to filter by the current user
    def get_queryset(self):
        return self.queryset.filter(employee=self.request.user)


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_manager

class ManagerLeaveHistoryView(generics.ListAPIView):
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated, IsManager]
    
    def get_queryset(self):
        # Return leave requests for employees who report to the current manager
        return LeaveRequest.objects.filter(employee__manager=self.request.user).order_by('-submission_date') 

class LeaveRequestListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = LeaveRequestSerializer
    
    def get_queryset(self):
        # Return pending leave requests for employees who report to the current manager
        return LeaveRequest.objects.filter(
            employee__manager=self.request.user,
            status="pending"
        ).order_by('-submission_date') 

class UpdateLeaveRequestStatusView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = LeaveRequestSerializer
    
    def get_queryset(self):
        # Only allow updates for leave requests from managed employees
        return LeaveRequest.objects.filter(
            employee__manager=self.request.user,
            status="pending"
        )
    
    def patch(self, request, *args, **kwargs):
        leave_request = self.get_object()
        
        if leave_request.status != "pending":
            raise ValidationError("Only pending requests can be updated.")
        
        action = request.data.get("action")
        
        if action == "approve":
            leave_request.status = "approved"
            message = "Leave request approved"
        elif action == "decline":
            leave_request.status = "rejected"
            message = "Leave request declined"
        else:
            raise ValidationError(
                "Invalid action provided. Must be 'approve' or 'decline'."
            )
        
        leave_request.save()
        return Response({"message": message}, status=status.HTTP_200_OK)

class ManagerLeaveReportView(APIView):
    permission_classes = [IsAuthenticated, IsManager]
    
    def get(self, request):
        leave_requests = LeaveRequest.objects.filter(employee__manager=request.user).order_by('-submission_date') 
        
        report_data = [
            {
                "employee": f"{leave.employee.first_name} {leave.employee.last_name}",
                "leave_type": leave.leave_type,
                "start_date": leave.start_date,
                "end_date": leave.end_date,
                "reason": leave.reason,
                "status": leave.status,
                "submission_date": leave.submission_date
            }
            for leave in leave_requests
        ]
        
        return Response({"report": report_data})

# View for generating a leave report for an individual employee
class EmployeeLeaveReportView(View):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch leave requests for the current user (employee)
        leave_requests = LeaveRequest.objects.filter(employee=request.user).order_by('-submission_date') 
        report_data = [
            {
                "leave_type": leave.leave_type,
                "date": leave.date,
                "reason": leave.reason,
                "status": leave.status,
            }
            for leave in leave_requests
        ]

        # Return the employee's leave report as JSON
        return JsonResponse({"report": report_data}, safe=False)


# API view to allow an employee to cancel a leave request
class CancelLeaveView(generics.UpdateAPIView):
    queryset = LeaveRequest.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = LeaveRequestSerializer

    def update(self, request, *args, **kwargs):
        # Extract the leave request ID from the request body
        leave_request_id = request.data.get("id")

        try:
            # Get the leave request instance by ID
            leave_request = self.get_queryset().get(id=leave_request_id)

            # Update the status of the leave request to 'cancelled'
            leave_request.status = "cancelled"
            leave_request.save()

            # Serialize the updated leave request and return the response
            serializer = self.get_serializer(leave_request)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except LeaveRequest.DoesNotExist:
            # Return a 404 response if the leave request is not found
            return Response(
                {"detail": "Leave request not found."}, status=status.HTTP_404_NOT_FOUND
            )