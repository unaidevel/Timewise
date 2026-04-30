from django.contrib import admin

from .models import TimeReportApprovalEventModel, TimeReportApprovalModel

admin.site.register(TimeReportApprovalModel)
admin.site.register(TimeReportApprovalEventModel)
