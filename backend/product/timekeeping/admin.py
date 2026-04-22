from django.contrib import admin

from product.timekeeping.models import PeriodModel, TimeReportModel, TimeEntryModel

admin.site.register(PeriodModel)
admin.site.register(TimeReportModel)
admin.site.register(TimeEntryModel)
