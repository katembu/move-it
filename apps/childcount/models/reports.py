#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

'''ChildCount Models


'''

from django.db import models
from django.utils.translation import ugettext as _

from reporters.models import Reporter
from childcount.models import Patient


class CCReport(models.Model):

    '''
    The highest level superclass to be inhereted by all other report classes
    '''

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"ChildCount Report")
        verbose_name_plural = _(u"ChildCount Reports")
        get_latest_by = ('modified_by',)

    created_by = models.ForeignKey(Reporter, verbose_name=_(u"Created by"), \
                                   related_name='created_report',
                                   help_text=_(u"Reporter that created the " \
                                                "report"))

    created_on = models.DateTimeField(_(u"Created on"), auto_now_add=True, \
                                      help_text=_(u"When the report was " \
                                                   "created"))

    modified_by = models.ForeignKey(Reporter, verbose_name=_(u"Modified by"), \
                                    related_name='modified_report',
                                    null=True, blank=True, \
                                    help_text=_(u"Reporter that last " \
                                                 "modified the report"))

    modified_on = models.DateTimeField(_(u"Modified on"), auto_now=True, \
                                       null=True, blank=True, \
                                       help_text=_(u"When the report was " \
                                                    "last modified"))


class PatientReport(CCReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Patient Report")
        verbose_name_plural = _(u"Patient Reports")

    patient = models.ForeignKey(Patient, verbose_name=_(u"Patient"))


class BirthReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Birth Report")
        verbose_name_plural = _(u"Birth Reports")

    CLINIC_DELIVERY_YES = 'Y'
    CLINIC_DELIVERY_NO = 'N'
    CLINIC_DELIVERY_UNKOWN = 'U'
    CLINIC_DELIVERY_CHOICES = (
        (CLINIC_DELIVERY_YES, _(u"Yes")),
        (CLINIC_DELIVERY_NO, _(u"No")),
        (CLINIC_DELIVERY_UNKOWN, _(u"Unknown")))

    clinic_delivery = models.CharField(_(u"Clinic delivery"), max_length=1, \
                                       choices=CLINIC_DELIVERY_CHOICES, \
                                       help_text=_(u"Was the baby born in " \
                                                    "a health facility?"))

    weight = models.FloatField(_(u"Birth weight"), null=True, blank=True, \
                               help_text=_(u"Birth weight in kg"))


class DeathReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Death Report")
        verbose_name_plural = _(u"Death Reports")

    death_date = models.DateField(_(u"Date of death"))


class StillbirthMiscarriageReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Stillbirth / Miscarriage Report")
        verbose_name_plural = _(u"Stillbirth / Miscarriage Reports")

    incident_date = models.DateField(_(u"Date of stillbirth or miscarriage"))


class FollowUpReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Follow-up Report")
        verbose_name_plural = _(u"Follow-up Reports")

    IMPROVEMENT_YES = 'Y'
    IMPROVEMENT_NO = 'N'
    IMPROVEMENT_UNKOWN = 'U'
    IMPROVEMENT_UNAVAILABLE = 'L'
    IMPROVEMENT_CHOICES = (
                       (IMPROVEMENT_YES, _('Yes')),
                       (IMPROVEMENT_NO, _('No')),
                       (IMPROVEMENT_UNKOWN, _('Unkown')),
                       (IMPROVEMENT_UNAVAILABLE, _('Patient unavailable')))

    VISITED_YES = 'Y'
    VISITED_NO = 'N'
    VISITED_UNKOWN = 'U'
    VISITED_INPATIENT = 'P'
    VISITED_CHOICES = (
                       (VISITED_YES, _('Yes')),
                       (VISITED_NO, _('No')),
                       (VISITED_UNKOWN, _('Unkown')),
                       (VISITED_INPATIENT, _('Patient currently inpatient')))

    improvement = models.CharField(_(u"Improvement"), max_length=1, \
                                   choices=IMPROVEMENT_CHOICES, \
                              help_text=_(u"Has the patient's condition " \
                                           "improved since last CHW visit?"))

    visited_clinic = models.CharField(_(u"Visited clinic"), max_length=1, \
                                   choices=VISITED_CHOICES, \
                              help_text=_(u"Did the patient visit a health "\
                                           "facility since last CHW visit?"))


class DangerSignsReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Danger Signs Report")
        verbose_name_plural = _(u"Danger Signs Reports")

    danger_signs = models.ManyToManyField('CodedItem', \
                                          verbose_name=_(u"Danger signs"))


class PregnancyReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Pregnancy Report")
        verbose_name_plural = _(u"Pregnancy Reports")

    pregnancy_month = models.PositiveSmallIntegerField(_(u"Months Pregnant"), \
                                    help_text=_(u"How many months into the " \
                                                 "pregnancy?"))
    anc_visits = models.PositiveSmallIntegerField(_(u"ANC Visits"), \
                                    help_text=_(u"Number of antenatal clinic "\
                                                 "visits during pregnancy"))
    weeks_since_anc = models.PositiveSmallIntegerField(\
                                        _(u"Weeks since last ANC visit"), \
                                        null=True, blank=True,
                            help_text=_(u"How many weeks since the patient's "\
                                         "last ANC visit (0 for less " \
                                         "than 7 days)"))


class NeonatalReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Neonatal Report")
        verbose_name_plural = _(u"Neonatal Reports")

    clinic_visits = models.PositiveSmallIntegerField(_(u"Clinic Visits"), \
                                    help_text=_(u"Number of clinic visits " \
                                                 "since birth"))


class UnderOneReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Under One Report")
        verbose_name_plural = _(u"Under One Reports")

    BREAST_YES = 'Y'
    BREAST_NO = 'N'
    BREAST_UNKOWN = 'U'
    BREAST_CHOICES = (
        (BREAST_YES, _(u"Yes")),
        (BREAST_NO, _(u"No")),
        (BREAST_UNKOWN, _(u"Unkown")))

    IMMUNIZED_YES = 'Y'
    IMMUNIZED_NO = 'N'
    IMMUNIZED_UNKOWN = 'U'
    IMMUNIZED_CHOICES = (
        (IMMUNIZED_YES, _(u"Yes")),
        (IMMUNIZED_NO, _(u"No")),
        (IMMUNIZED_UNKOWN, _(u"Unkown")))


    breast_only = models.CharField(_(u"Breast feeding Only"), max_length=1, \
                                   choices=BREAST_CHOICES, \
                                   help_text=_(u"Does the mother breast " \
                                                "feed only?"))

    immunized = models.CharField(_(u"Immunized"), max_length=1, \
                                   choices=IMMUNIZED_CHOICES, \
                                   help_text=_(u"Is the child up-to-date on" \
                                                "immunizations?"))


class NutritionReport(PatientReport):

    '''record nutrition related measurements'''

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Nutrition Report")
        verbose_name_plural = _(u"Nutrition Reports")

    STATUS_MODERATE = 1
    STATUS_SEVERE = 2
    STATUS_SEVERE_COMP = 3
    STATUS_HEALTHY = 4

    STATUS_CHOICES = (
        (STATUS_MODERATE, _(u"MAM")),
        (STATUS_SEVERE, _(u"SAM")),
        (STATUS_SEVERE_COMP, _(u"SAM+")),
        (STATUS_HEALTHY, _(u"Healthy")))

    OEDEMA_YES = 'Y'
    OEDEMA_NO = 'N'
    OEDEMA_UNKOWN = 'U'
    OEDEMA_CHOICES = (
        (OEDEMA_YES, _(u"Yes")),
        (OEDEMA_NO, _(u"No")),
        (OEDEMA_UNKOWN, _(u"Unknown")))

    muac = models.SmallIntegerField(_(u"MUAC (mm)"), blank=True, null=True)
    oedema = models.CharField(_(u"Oedema"), max_length=1, \
                              choices=OEDEMA_CHOICES)
    weight = models.FloatField(_(u"Weight (kg)"), blank=True, null=True)
    status = models.IntegerField(_("Status"),\
                                 choices=STATUS_CHOICES, blank=True, null=True)

    def diagnose(self):
        '''Diagnosis of the patient'''
        self.status = self.STATUS_HEALTHY
        if self.oedema == 'Y' or self.muac < 110:
            self.status = self.STATUS_SEVERE
        elif self.muac < 125:
            self.status = self.STATUS_MODERATE

    def save(self, *args):
        if self.status is None:
            self.diagnose()
        super(NutritionReport, self).save(*args)

    @property
    def verbose_state(self):
        for k, v in self.STATUS_CHOICES:
            if self.status == k:
                return v


class FeverReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Fever Report")
        verbose_name_plural = _(u"Fever Reports")

    RDT_POSITIVE = 'P'
    RDT_NEGATIVE = 'N'
    RDT_UNKOWN = 'U'
    RDT_UNAVAILABLE = 'X'

    RDT_CHOICES = (
        (RDT_POSITIVE, _(u"Positive")),
        (RDT_NEGATIVE, _(u"Negative")),
        (RDT_UNKOWN, _(u"Unknown")),
        (RDT_UNAVAILABLE, _(u"Test unavailable")))

    rdt_result = models.CharField(_(u"RDT Result"), max_length=1, \
                                  choices=RDT_CHOICES)


class MedicineGivenReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Medicine Given Report")
        verbose_name_plural = _(u"Medicine Given Reports")

    medicines = models.ManyToManyField('CodedItem', \
                                         verbose_name=_(u"Medicines"))


class ReferralReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Referral Report")
        verbose_name_plural = _(u"Referral Reports")

    URGENCY_AMBULANCE = 'A'
    URGENCY_EMERGENCY = 'E'
    URGENCY_BASIC = 'B'
    URGENCY_CONVENIENT = 'C'
    URGENCY_CHOICES = (
                       (URGENCY_AMBULANCE, _('Ambulance Referral')),
                       (URGENCY_EMERGENCY, _('Emergency Referral')),
                       (URGENCY_BASIC, _('Basic Referral')),
                       (URGENCY_CONVENIENT, _('Convenient Referral')))

    urgency = models.CharField(_(u"Urgency"), max_length=1, \
                               choices=URGENCY_CHOICES)


class HouseHoldVisitReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Household Visit Report")
        verbose_name_plural = _(u"Household Visit Reports")

    available = models.BooleanField(_(u"HH Member Available"), \
                                help_text=_(u"Was a houshold member " \
                                             "available?"))

    children = models.SmallIntegerField(_("Children under five"), \
                                        blank=True, null=True, 
                            help_text=_("Number of children under 5 seen"))

    counseling = models.ManyToManyField('CodedItem', \
                        verbose_name=_(u"Counseling / advice topics covered"))


class FamilyPlanningReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Family Planning Report")
        verbose_name_plural = _(u"Family Planning Reports")

    women = models.PositiveSmallIntegerField(_(u"Women"), \
                            help_text=_(u"Number of women aged 15 to 49 " \
                                         "seen during visit"))

    women_using = models.PositiveSmallIntegerField(_(u"Women using FP"), \
                            help_text=_(u"Number of the women using " \
                                         "modern family planning"))


class BedNetReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Bednet Report")
        verbose_name_plural = _(u"Bednet Reports")

    nets = models.PositiveSmallIntegerField(_(u"Bednets"),\
                            help_text=_(u"Number of functioning bednets " \
                                         "in the household"))

    sleeping_sites = models.PositiveSmallIntegerField(_(u"Sleeping sites"),\
                            help_text=_(u"Number of sleeping sites"))
