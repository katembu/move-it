#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

from django.contrib import admin

from childcount.models import *
from childcount.models.reports import *

admin.site.register(Configuration)
admin.site.register(CHW)
admin.site.register(Clinic)
admin.site.register(Patient)

#Reports
admin.site.register(CCReport)
admin.site.register(PatientReport)
admin.site.register(BirthReport)
admin.site.register(DeathReport)
admin.site.register(StillbirthMiscarriageReport)
admin.site.register(FollowUpReport)
admin.site.register(PregnancyReport)
admin.site.register(NeonatalReport)
admin.site.register(UnderOneReport)
admin.site.register(NutritionReport)
admin.site.register(FeverReport)
admin.site.register(ReferralReport)
admin.site.register(HouseHoldVisitReport)
admin.site.register(FamilyPlanningReport)
admin.site.register(FamilyPlanningUsage)
admin.site.register(BedNetReport)
admin.site.register(DangerSignsReport)
admin.site.register(MedicineGivenReport)
admin.site.register(CodedItem)
admin.site.register(CodedItemTranslation)

admin.site.register(Case)
admin.site.register(Referral)










