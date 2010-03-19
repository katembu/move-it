#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

'''ChildCount Models


'''

from django.db import models
from django.utils.translation import ugettext as _
import reversion
from reversion.models import Version

from polymorphic import PolymorphicModel

from childcount.models import Patient
from childcount.models import Encounter


class CCReport(PolymorphicModel):

    '''
    The highest level superclass to be inhereted by all other report classes
    '''

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"ChildCount Report")
        verbose_name_plural = _(u"ChildCount Reports")

    encounter = models.ForeignKey(Encounter, verbose_name=_(u"Encounter"))

    def reset(self):
        self.__init__(pk=self.pk, encounter=self.encounter)

    def patient(self):
        return encounter.patient

    def chw(self):
        return encounter.chw

    def inital_version(self):
        return Version.objects.get_for_object(self)[0]

    def current_version(self):
        return Version.objects.get_for_object(self).\
                                      order_by('-revision__date_created')[0]

    def entered_by(self):
        return self.initial_version().revision.user

    def entered_on(self):
        return self.initial_version().revision.date_created

    def modified(self):
        return Version.objects.get_for_object(self).count() > 1

    def modified_by(self):
        if not self.modified():
            return None
        return self.current_version().revision.user

    def modified_on(self):
        if not self.modified():
            return None
        return self.current_version().revision.date_created

    def __unicode__(self):
        string = u"%s %s" % (self.encounter, self.__class__.__name__)
        try:
            string += " - %s" % self.summary()
        except AttributeError:
            pass
        return string

    def get_omrs_dict(self):
        '''OpenMRS Key/Value dict.

        Return key/value dictionary of openmrs values that this report can
        populate
        '''
        return {}

reversion.register(CCReport)


class BirthReport(CCReport):

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

    weight = models.FloatField(_(u"Birth weight (kg)"), null=True, blank=True)

    def summary(self):
        string = u"%s: %s" % \
            (self._meta.get_field_by_name('clinic_delivery')[0].verbose_name, \
             self.get_clinic_delivery_display())
        if self.weight:
            string += ", %s: %s" % \
                    (self._meta.get_field_by_name('weight')[0].verbose_name, \
                     self.weight)
        return string                 
reversion.register(BirthReport, follow=['ccreport_ptr'])


class DeathReport(CCReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Death Report")
        verbose_name_plural = _(u"Death Reports")

    death_date = models.DateField(_(u"Date of death"))

    def summary(self):
        return u"%s: %s" % \
                (self._meta.get_field_by_name('death_date')[0].verbose_name, \
                 self.death_date)
reversion.register(DeathReport)


class StillbirthMiscarriageReport(CCReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Stillbirth / Miscarriage Report")
        verbose_name_plural = _(u"Stillbirth / Miscarriage Reports")

    incident_date = models.DateField(_(u"Date of stillbirth or miscarriage"))

    def summary(self):
        return u"%s: %s" % \
             (self._meta.get_field_by_name('incident_date')[0].verbose_name, \
              self.incident_date)
reversion.register(StillbirthMiscarriageReport, follow=['ccreport_ptr'])


class FollowUpReport(CCReport):

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

    def summary(self):
        return u"%s: %s, %s: %s" % \
            (self._meta.get_field_by_name('improvement')[0].verbose_name, \
             self.get_improvement_display(),
             self._meta.get_field_by_name('visited_clinic')[0].verbose_name, \
             self.get_visited_clinic_display())
reversion.register(FollowUpReport, follow=['ccreport_ptr'])


class DangerSignsReport(CCReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Danger Signs Report")
        verbose_name_plural = _(u"Danger Signs Reports")

    danger_signs = models.ManyToManyField('CodedItem', \
                                          verbose_name=_(u"Danger signs"))

    def summary(self):
        return u"%s: %s" % \
            (self._meta.get_field_by_name('danger_signs')[0].verbose_name, \
             u", ".join([ds.description for ds in self.danger_signs.all()]))
reversion.register(DangerSignsReport, follow=['ccreport_ptr'])


class PregnancyReport(CCReport):

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

    def summary(self):
        string = u"%s: %d, %s: %d" % \
            (self._meta.get_field_by_name('pregnancy_month')[0].verbose_name, \
             self.pregnancy_month,
             self._meta.get_field_by_name('anc_visits')[0].verbose_name, \
             self.anc_visits)
        if self.weeks_since_anc:
            string += ", %s: %d" % \
            (self._meta.get_field_by_name('weeks_since_anc')[0].verbose_name, \
             self.weeks_since_anc)
        return string
reversion.register(PregnancyReport, follow=['ccreport_ptr'])


class NeonatalReport(CCReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Neonatal Report")
        verbose_name_plural = _(u"Neonatal Reports")

    clinic_visits = models.PositiveSmallIntegerField(_(u"Clinic Visits"), \
                                    help_text=_(u"Number of clinic visits " \
                                                 "since birth"))

    def summary(self):
        return u"%s: %d" % \
             (self._meta.get_field_by_name('clinic_visits')[0].verbose_name, \
              self.clinic_visits)
reversion.register(NeonatalReport, follow=['ccreport_ptr'])


class UnderOneReport(CCReport):

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

    def summary(self):
        return u"%s: %s, %s: %s" % \
            (self._meta.get_field_by_name('breast_only')[0].verbose_name, \
             self.get_breast_only_display(),
             self._meta.get_field_by_name('immunized')[0].verbose_name, \
             self.get_immunized_display())
reversion.register(UnderOneReport, follow=['ccreport_ptr'])


class NutritionReport(CCReport):

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

    def summary(self):
        strings = []
        if self.muac:
            strings.append(u"%s: %s" %
                    (self._meta.get_field_by_name('muac')[0].verbose_name, \
                     self.muac))
        strings.append(u"%s: %s" %
                (self._meta.get_field_by_name('oedema')[0].verbose_name, \
                 self.get_oedema_display()))
        if self.weight:
            strings.append(u"%s: %s" %
                    (self._meta.get_field_by_name('weight')[0].verbose_name, \
                     self.weight))
        if self.status:
            strings.append(u"%s: %s" %
                    (self._meta.get_field_by_name('status')[0].verbose_name, \
                     self.get_status_display()))
        return u", ".join(strings)

    @property
    def verbose_state(self):
        for k, v in self.STATUS_CHOICES:
            if self.status == k:
                return v
reversion.register(NutritionReport, follow=['ccreport_ptr'])


class FeverReport(CCReport):

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

    def summary(self):
        return u"%s: %s" % \
            (self._meta.get_field_by_name('rdt_result')[0].verbose_name, \
             self.get_rdt_result_display())
reversion.register(FeverReport, follow=['ccreport_ptr'])


class MedicineGivenReport(CCReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Medicine Given Report")
        verbose_name_plural = _(u"Medicine Given Reports")

    medicines = models.ManyToManyField('CodedItem', \
                                         verbose_name=_(u"Medicines"))

    def summary(self):
        return u"%s: %s" % \
            (self._meta.get_field_by_name('medicines')[0].verbose_name, \
             u", ".join([ds.description for ds in self.medicines.all()]))
reversion.register(MedicineGivenReport, follow=['ccreport_ptr'])


class ReferralReport(CCReport):

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

    def summary(self):
        return u"%s: %s" % \
            (self._meta.get_field_by_name('urgency')[0].verbose_name, \
             self.get_urgency_display())
reversion.register(ReferralReport, follow=['ccreport_ptr'])


class HouseHoldVisitReport(CCReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Household Visit Report")
        verbose_name_plural = _(u"Household Visit Reports")

    available = models.BooleanField(_(u"HH Member Available"), \
                                help_text=_(u"Was a houshold member " \
                                             "available?"))

    children = models.SmallIntegerField(_("Children under five"), \
                                        blank=True, null=True, \
                            help_text=_("Number of children under 5 seen"))

    counseling = models.ManyToManyField('CodedItem', \
                       verbose_name=_(u"Counseling / advice topics covered"), \
                       blank=True)

    def summary(self):
        string = u"%s: %s" % \
                (self._meta.get_field_by_name('available')[0].verbose_name, \
                 bool(self.available))
        if self.available and self.children is not None:
            string += ", %s: %d" % \
                (self._meta.get_field_by_name('children')[0].verbose_name, \
                 self.children)
        return string
reversion.register(HouseHoldVisitReport, follow=['ccreport_ptr'])


class FamilyPlanningReport(CCReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Family Planning Report")
        verbose_name_plural = _(u"Family Planning Reports")

    women = models.PositiveSmallIntegerField(_(u"Women"), \
                            help_text=_(u"Number of women aged 15 to 49 " \
                                         "seen during visit"))

    women_using = models.PositiveSmallIntegerField(_(u"Women using FP"), \
                                                null=True, blank=True, \
                            help_text=_(u"Number of the women using " \
                                         "modern family planning"))

    def summary(self):
        string = u"%s: %d" % \
                    (self._meta.get_field_by_name('women')[0].verbose_name, \
                     self.women)
        if self.women_using is not None:
            string += ", %s: %d" % (self._meta.get_field_by_name(\
                                            'women_using')[0].verbose_name, \
                                   self.women_using)
            if self.familyplanningusage_set.all().count() > 0:
                string += " (%s)" % \
                            ", ".join([unicode(fpu) for fpu in \
                                        self.familyplanningusage_set.all()])
        return string

reversion.register(FamilyPlanningReport, \
                   follow=['ccreport_ptr', 'familyplanningusage_set'])


class BedNetReport(CCReport):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Bednet Report")
        verbose_name_plural = _(u"Bednet Reports")

    nets = models.PositiveSmallIntegerField(_(u"Bednets"), \
                            help_text=_(u"Number of functioning bednets " \
                                         "in the household"))

    sleeping_sites = models.PositiveSmallIntegerField(_(u"Sleeping sites"),\
                            help_text=_(u"Number of sleeping sites"))

    def summary(self):
        return u"%s: %d, %s: %d" % \
            (self._meta.get_field_by_name('nets')[0].verbose_name, \
             self.nets,
             self._meta.get_field_by_name('sleeping_sites')[0].verbose_name, \
             self.sleeping_sites)
reversion.register(BedNetReport, follow=['ccreport_ptr'])
