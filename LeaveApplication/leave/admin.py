from django.contrib import admin
from .models import LeaveRequest,Holiday

# Register your models here.
admin.site.register(LeaveRequest)
admin.site.register(Holiday)