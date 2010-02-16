#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

'''ChildCount Models

CCReport (superclass)
NonPatientRDTReport
PatientReport (superclass)
HealthReport
DeathReport
PatientRegistrationReport
HouseHoldVisitReport
FeverReport
PregnancyReport
PostPartumReport
BirthReport
NewbornReport
ChildReport
DispensationReport
MUACReport


'''

from django.db import models
from django.utils.translation import ugettext as _

from reporters.models import Reporter

from childcount.models import DangerSign
from childcount.models import Patient
#from childcount.models import Commodity

from childcount.models.shared_fields import RDTField, GenderField
from childcount.models.shared_fields import DangerSignsField


class CCReport(models.Model):

    '''
    The highest level superclass to be inhereted by all other report classes
    '''

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"ChildCount Report")
        verbose_name_plural = _(u"ChildCount Reports")

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


class NonPatientRDTReport(CCReport, RDTField, GenderField):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Non-patient RDT Report")
        verbose_name_plural = _(u"Non-patient RDT Reports")

    age = models.PositiveSmallIntegerField(_(u"Age"), help_text=_(u"Age in " \
                                                                   "years"))


class PatientReport(CCReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Patient Report")
        verbose_name_plural = _(u"Patient Reports")

    patient = models.ForeignKey(Patient, verbose_name=_(u"Patient"))


class HealthReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Health Report")
        verbose_name_plural = _(u"Health Reports")

    DANGER_SIGNS_PRESENT = 'S'
    DANGER_SIGNS_NONE = 'N'
    DANGER_SIGNS_UNKOWN = 'U'
    DANGER_SIGNS_UNAVAILABLE = 'W'

    DANGER_SIGNS_CHOICES = (
        (DANGER_SIGNS_PRESENT, _(u"Present")),
        (DANGER_SIGNS_NONE, _(u"None")),
        (DANGER_SIGNS_UNKOWN, _(u"Unknown")),
        (DANGER_SIGNS_UNAVAILABLE, _(u"Unavailable")))

    VISITED_CLINIC_YES = 'Y'
    VISITED_CLINIC_NO = 'N'
    VISITED_CLINIC_UNKOWN = 'U'
    VISITED_CLINIC_INPATIENT = 'K'

    VISITED_CLINIC_CHOICES = (
        (VISITED_CLINIC_YES, _(u"Yes")),
        (VISITED_CLINIC_NO, _(u"None")),
        (VISITED_CLINIC_UNKOWN, _(u"Unknown")),
        (VISITED_CLINIC_INPATIENT, _(u"Currently inpatient")))

    danger_signs = models.CharField(_(u"Danger Signs"), max_length=1, \
                                    choices=DANGER_SIGNS_CHOICES)

    visited_clinic = models.CharField(_(u"Recent Clinic Visit"), max_length=1,\
                                      choices=VISITED_CLINIC_CHOICES, \
                                      help_text=_(u"Did the patient visit a " \
                                                   "health facility since " \
                                                   "the last CHW visit"))


class DeathReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Death Report")
        verbose_name_plural = _(u"Death Reports")

    death_date = models.DateField(_(u"Date of death"), \
                                  help_text=_(u"The date of the death " \
                                               "accurate to within the month"))


class ReferralReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Referral Report")
        verbose_name_plural = _(u"Referral Reports")

    URGENCY_AMBULANCE = 'A'
    URGENCY_BASIC = 'B'
    URGENCY_CONVENIENT = 'C'
    URGENCY_CHOICES = (
                       (URGENCY_AMBULANCE, _('Ambulance Referral')),
                       (URGENCY_BASIC, _('Basic Referral')),
                       (URGENCY_CONVENIENT, _('Convenient Referral')))

    danger_signs = models.ManyToManyField(DangerSign, \
                                          verbose_name=_(u"Danger signs"))
    urgency = models.CharField(max_length=1, choices=URGENCY_CHOICES)


class DangerSignReport(PatientReport):
    
    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"DangerSign Report")
        verbose_name_plural = _(u"DangerSign Reports")

    danger_signs = models.ManyToManyField(DangerSign, \
                                          verbose_name=_(u"Danger signs"))


class PatientRegistrationReport(PatientReport):
    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Patient Registration Report")
        verbose_name_plural = _(u"Patient Registration Reports")


class HouseHoldVisitReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Household Visit Report")
        verbose_name_plural = _(u"Household Visit Reports")

    available = models.BooleanField(_(u"HH Member Available"), \
                                help_text=_(u"Was a houshold member " \
                                             "available?"))
    pregnant = models.SmallIntegerField(_("Number of pregnant women"), \
                                        help_text=_("what was the number of "\
                                                    "pregnant women?"), \
                                        blank=True, null=True)
    underfive = models.SmallIntegerField(_("Number of Under Five children"), \
                                        help_text=_("what was the number of "\
                                                    "Under Five children?"), \
                                        blank=True, null=True)
    danger_signs = models.ManyToManyField(DangerSign)


class FeverReport(PatientReport, RDTField):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Fever Report")
        verbose_name_plural = _(u"Fever Reports")


class DiarrheaReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Diarrhea Report")
        verbose_name_plural = _(u"Diarrhea Reports")

    '''
    HOME_YES = 'Y'
    HOME_NO = 'N'
    HOME_UNKNOWN = 'U'
    HOME_CHOICES = (
                    (HOME_YES, _(u"Yes")),
                    (HOME_NO, _(u"Yes")),
                    (HOME_UNKNOWN, _(u"Yes"))
                    )

    home_treatment = models.CharField(_(u"Home treated?"), \
                                      max_length=1, \
                                      choices=HOME_CHOICES,
                                      help_text=_(u"Is Patient eligible for "\
                                                  "home treatment"))
    '''
    TREATMENT_ORS = 'R'
    TREATMENT_ZINC = 'Z'
    TREATMENT_CHOICES = (
                    (TREATMENT_ORS, _(u"ORS")),
                    (TREATMENT_ZINC, _(u"ZINC")),
                    )

    treatment = models.CharField(_("Treatment"), max_length=1, \
                                 choices=TREATMENT_CHOICES, \
                                 help_text=_("what treatment was given?(ORS "\
                                             "or Zinc)"))


class PregnancyReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Pregnancy Report")
        verbose_name_plural = _(u"Pregnancy Reports")

    pregnancy_month = models.PositiveSmallIntegerField(_(u"Months Pregnant"), \
                                    help_text=_(u"How many months into the " \
                                                 "pregnancy?"))
    clinic_visits = models.PositiveSmallIntegerField(_(u"Clinic Visits"), \
                                    help_text=_(u"Number of clinic visits " \
                                                 "during pregnancy"))


class PostpartumReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Postpartum Report")
        verbose_name_plural = _(u"Postpartum Reports")

    clinic_visits = models.PositiveSmallIntegerField(_(u"Clinic Visits"), \
                                    help_text=_(u"Number of clinic visits " \
                                                 "since delivery"))


class NeonatalReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Neonatal Report")
        verbose_name_plural = _(u"Neonatal Reports")

    clinic_visits = models.PositiveSmallIntegerField(_(u"Clinic Visits"), \
                                    help_text=_(u"Number of clinic visits " \
                                                 "since delivery"))


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

    BCG_YES = 'Y'
    BCG_NO = 'N'
    BCG_UNKOWN = 'U'
    BCG_CHOICES = (
        (BCG_YES, _(u"Yes")),
        (BCG_NO, _(u"No")),
        (BCG_UNKOWN, _(u"Unknown")))

    SMALL_YES = 'Y'
    SMALL_NO = 'N'
    SMALL_UNKOWN = 'U'
    SMALL_CHOICES = (
        (SMALL_YES, _(u"Yes")),
        (SMALL_NO, _(u"No")),
        (SMALL_UNKOWN, _(u"Unknown")))

    clinic_delivery = models.CharField(_(u"Clinic delivery"), max_length=1, \
                                       choices=CLINIC_DELIVERY_CHOICES, \
                                       help_text=_(u"Was the baby born in " \
                                                    "a health facility?"))

    bcg = models.CharField(_(u"BCG immunisation"), max_length=1, \
                           choices=CLINIC_DELIVERY_CHOICES, \
                           help_text=_(u"Has the baby received the BCG " \
                                        "vaccination?"))

    weight = models.FloatField(_(u"Birth Weight"), null=True, blank=True, \
                             help_text=_(u"What was the weight of the baby '\
                             'at birth?"))


class NewbornReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Newborn Report")
        verbose_name_plural = _(u"Newborn Reports")

    BREAST_YES = 'Y'
    BREAST_NO = 'N'
    BREAST_UNKOWN = 'U'
    BREAST_CHOICES = (
        (BREAST_YES, _(u"Yes")),
        (BREAST_NO, _(u"No")),
        (BREAST_UNKOWN, _(u"Unkown")))

    clinic_vists = models.PositiveSmallIntegerField(_(u"Clinic visits"), \
                                               help_text=_(u"Number of " \
                                                            "clinic visits " \
                                                            "since birth"))

    breast_only = models.CharField(_(u"Breast feeding Only"), max_length=1, \
                                   choices=BREAST_CHOICES, \
                                   help_text=_(u"Does the mother breast " \
                                                "feed only?"))


class ChildReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Child Report")
        verbose_name_plural = _(u"Child Reports")

    FEVER_YES = 'F'
    FEVER_NO = 'N'
    FEVER_UNKOWN = 'U'
    FEVER_CHOICES = (
        (FEVER_YES, _(u"Yes")),
        (FEVER_NO, _(u"No")),
        (FEVER_UNKOWN, _(u"Unknown")))

    DIARRHEA_YES = 'D'
    DIARRHEA_NO = 'N'
    DIARRHEA_UNKOWN = 'U'
    DIARRHEA_CHOICES = (
        (DIARRHEA_YES, _(u"Yes")),
        (DIARRHEA_NO, _(u"No")),
        (DIARRHEA_UNKOWN, _(u"Unknown")))

    fever = models.CharField(_(u"Fever"), max_length=1, \
                             choices=FEVER_CHOICES, \
                             help_text=_(u"Has the child had a fever in the " \
                                          "past 3 days? "))

    diarrhea = models.CharField(_(u"Diarrhea"), max_length=1, \
                                choices=DIARRHEA_CHOICES, \
                                help_text=_(u"Has the child had diarrhea in " \
                                             "the past 24 hours? "))


class DispensationReport(PatientReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Dispensation Report")
        verbose_name_plural = _(u"Dispensation Reports")

    commodities = models.ManyToManyField('Commodity', \
                                         verbose_name=_(u"Commodities"))


class MUACReport(PatientReport):

    '''record malnutrition measurements'''

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"MUAC Report")
        verbose_name_plural = _(u"MUAC Reports")

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

    muac = models.SmallIntegerField(_(u"MUAC (mm)"))
    oedema = models.CharField(_(u"Oedema"), max_length=1, \
                              choices=OEDEMA_CHOICES)
    status = models.IntegerField(_("Status"),\
                                 choices=STATUS_CHOICES, db_index=True, \
                                 blank=True, null=True)
    weight = models.FloatField(_("Weight"), blank=True, null=True)

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
        super(MUACReport, self).save(*args)
