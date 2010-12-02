#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.utils.translation import gettext as _

from django.db.models import F
from django.db.models import Avg, Count, Sum

import calendar
from datetime import datetime
from datetime import date
from datetime import time
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from childcount.models import Patient
from locations.models import Location
from childcount.models import CHW, Clinic
from childcount.models import NutritionReport
from childcount.models import MedicineGivenReport
from childcount.models import DangerSignsReport
from childcount.models import NeonatalReport
from childcount.models import FamilyPlanningReport
from childcount.models import FeverReport
from childcount.models import CodedItem
from childcount.models import ReferralReport
from childcount.models import BirthReport
from childcount.models import PregnancyReport
from childcount.models import HouseholdVisitReport
from childcount.models import FollowUpReport
from childcount.models import ImmunizationSchedule
from childcount.models import ImmunizationNotification
from childcount.models import BedNetReport
from childcount.models import BednetIssuedReport
from childcount.models import BednetUtilization
from childcount.models import DrinkingWaterReport
from childcount.models import SanitationReport
from childcount.models import UnderOneReport

from childcount.utils import day_end, \
                                day_start, \
                                get_dates_of_the_week, \
                                get_median, \
                                seven_days_to_date, \
                                first_day_of_month, \
                                last_day_of_month, \
                                first_date_of_week
from childcount.reports.utils import reporting_week_sunday
from childcount.reports.utils import reporting_week_monday
from childcount.reports.indicator import Indicator

from logger_ng.models import LoggedMessage


class ThePatient(Patient):

    class Meta:
        verbose_name = _("Patient List Report")
        proxy = True

    def latest_muac(self):
        muac = NutritionReport.objects.filter(encounter__patient=self).latest()
        if not None:
            return u"%smm %s" % (muac.muac, muac.verbose_state)
        return u""

    def check_visit_within_seven_days_of_birth(self):
        seven_days_after_birth = self.dob + timedelta(7)
        hvr = HouseholdVisitReport.objects\
                .filter(encounter__encounter_date__gt=self.dob, \
                    encounter__encounter_date__lte=seven_days_after_birth)\
                .count()
        if hvr:
            return True
        else:
            return False

    def visit_within_90_days_of_last_visit(self):
        try:
            hvr = HouseholdVisitReport.objects\
                        .filter(encounter__patient=self.household).latest()
            latest_date = hvr.encounter.encounter_date
            old_date = latest_date - timedelta(90)
            hvr = HouseholdVisitReport.objects\
                        .filter(encounter__patient=self.household, \
                                encounter__encounter_date__gte=old_date, \
                                encounter__encounter_date__lt=latest_date)
            if hvr.count():
                return True
            return False
        except HouseholdVisitReport.DoesNotExist:
            return False

    def ontime_muac(self):
        try:
            nr = NutritionReport.objects\
                    .filter(encounter__patient=self).latest()
            latest_date = nr.encounter.encounter_date
            old_date = latest_date - timedelta(90)
            nr = NutritionReport.objects.filter(encounter__patient=self, \
                                encounter__encounter_date__gte=old_date, \
                                encounter__encounter_date__lt=latest_date)
            if nr.count():
                return True
            return False
        except NutritionReport.DoesNotExist:
            return False

    def status_text(self):
        ''' Return the text in status choices '''
        if not self.pk:
            return ''
        #TODO There is a smarter way of doing this, get it done
        for status in self.STATUS_CHOICES:
            if self.status in status:
                return status[1]
        return ''

    def generate_schedule(self):
        'Generate immunization '
        schedule = ImmunizationSchedule.objects.all()
        for period in schedule:
            patient_dob = self.dob
            notify_on = datetime.today()
            immunization = ImmunizationNotification()
            if not ImmunizationNotification.objects.filter(patient=self, \
                                                        immunization=period):
                immunization.patient = self
                immunization.immunization = period
                if period.period_type == ImmunizationSchedule.PERIOD_DAYS:
                    notify_on = patient_dob + timedelta(period.period)
                    immunization.notify_on = notify_on
                if period.period_type == ImmunizationSchedule.PERIOD_WEEKS:
                    notify_on = patient_dob + timedelta(period.period * 7)
                    immunization.notify_on = notify_on
                if period.period_type == ImmunizationSchedule.PERIOD_MONTHS:
                    notifyon = patient_dob + timedelta(30.4375 * period.period)
                    immunization.notify_on = notifyon

                immunization.save()

    def survey(self):
        #Get aggregate of bednets survey questions per chw
        survey = []
        try:
            bednet = BedNetReport.objects.get(encounter__patient=self)
            survey = ({'damaged': bednet.damaged_nets,
                       'function': bednet.function_nets,
                       'num_site': bednet.sleeping_sites,
                       'earlier': bednet.earlier_nets})
        except:
            pass

        #Get sanitation report
        try:
            san = SanitationReport.objects.get(encounter__patient=self)
            survey.update({'toilet_type': san.toilet_lat})
            if san.share_toilet is SanitationReport.U:
                survey.update({'share': 'U'})
            elif san.share_toilet is SanitationReport.PB:
                survey.update({'share': 'PB'})
            else:
                survey.update({'share': san.share_toilet})
        except:
            pass

        #Get drinking water report
        try:
            dwr = DrinkingWaterReport.objects.get(encounter__patient=self)
            survey.update({'water_source': dwr.water_source,
                           'treat_method': dwr.treatment_method})
        except:
            pass

        #get bednet utilization
        try:
            bedutil = BednetUtilization.objects.get(encounter__patient=self)
            survey.update({'under_five': bedutil.child_underfive,
                           'slept_bednet': bedutil.child_lastnite,
                           'hanging': bedutil.hanging_bednet,
                           'reason': bedutil.reason})
        except:
            pass

        for item in survey:
            if survey[item] is None:
                survey[item] = '-'
        return survey

    def required_bednet(self):
        try:
            total = self.survey()['num_site'] - self.survey()['function']
        except:
            total = '-'

        return total

    def household_members(self):
        return ThePatient.objects.filter(household=self.household)

    @classmethod
    def under_five(cls, chw=None):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        if chw:
            p = cls.objects.filter(dob__gte=sixtym, \
                                       chw=chw).order_by("household")
        else:
            p = cls.objects.filter(dob__gte=sixtym).order_by("household")
        return p

    @classmethod
    def patients_summary_list(cls):
        columns = []
        columns.append(
            {'name': cls._meta.get_field('household').verbose_name.upper(), \
            'bit': '{{object.household.health_id.upper}}'})
        columns.append(
            {'name': cls._meta.get_field('health_id').verbose_name.upper(), \
            'bit': '{{object.health_id.upper}}'})
        columns.append(
            {'name': _("Name".upper()), \
            'bit': '{{object.last_name}}{% if object.pk %},{% endif %} {{object.first_name}}'})
        columns.append(
            {'name': cls._meta.get_field('gender').verbose_name.upper(), \
            'bit': '{{object.gender}}'})
        columns.append(
            {'name': _("Age".upper()), \
            'bit': '{{object.humanised_age}}'})
        columns.append(
            {'name': _("Last MUAC".upper()), \
            'bit': '{{object.latest_muac}}'})
        columns.append(
            {'name': cls._meta.get_field('chw').verbose_name.upper(), \
            'bit': '{{object.chw}}'})

        sub_columns = None
        return columns, sub_columns

    def patient_register_columns(cls):
        columns = []
        columns.append(
            {'name': _(u"LOC"), \
            'bit': 
                '{% if object.is_head_of_household %}<strong>' \
                '{{ object.household.location.code }}' \
                '</strong>{% endif %}'})
        columns.append(
            {'name': _(u"HID"), \
            'bit': 
                '{% if object.is_head_of_household %}<strong>{% endif %}' \
                '{{object.health_id.upper}}' \
                '{% if object.is_head_of_household %}</strong>{% endif %}'})
        columns.append(
            {'name': _(u"Name".upper()), \
            'bit': '{{object.last_name}}{% if object.pk %},{% endif %} {{object.first_name}}'})
        columns.append(
            {'name': _(u"Gen."), \
            'bit': '{{object.gender}}'})
        columns.append(
            {'name': _(u"Age".upper()), \
            'bit': '{{object.humanised_age}}'})
        columns.append(
            {'name': _(u"Status".upper()), \
            'bit': '{{object.status_text}}'})
        #columns.append(
        #    {'name': _(u"HHID".upper()), \
        #    'bit': '{{object.household.health_id.upper}}'})
        return columns

    @classmethod
    def bednet_summary(cls):
        columns = []
        columns.append(
            {'name': _("Household ".upper()),
            'bit': '{{object.household.health_id.upper}}'})
        columns.append(
            {'name': cls._meta.get_field('location').verbose_name.upper(), \
             'bit': '{{ object.location }}'})
        columns.append(
            {'name': _("Household Name".upper()), \
             'bit': '{{ object.first_name }} {{ object.last_name }}'})
        columns.append(
            {'name': _("No. Sleeping site".upper()),
             'bit': '{{object.survey.num_site}}'})
        columns.append(
            {'name': _("Functioning Bednet".upper()),
             'bit': '{{object.survey.function}}'})
        columns.append(
            {'name': _("Earlier Bednets".upper()),
             'bit': '{{object.survey.earlier}}'})
        columns.append(
            {'name': _("Damaged Bednet".upper()),
             'bit': '{{object.survey.damaged}}'})
        columns.append(
            {'name': _("Required Bednets".upper()),
             'bit': '{{object.required_bednet}}'})
        columns.append(
            {'name': _("#under five last night".upper()),
             'bit': '{{object.survey.under_five}}'})
        columns.append(
            {'name': _("#slept on Bednet".upper()),
             'bit': '{{object.survey.slept_bednet}}'})
        columns.append(
            {'name': _("Hanging Bednet".upper()),
             'bit': '{{object.survey.hanging}}'})
        columns.append(
            {'name': _("Reason ".upper()),
             'bit': '{{object.survey.reason}}'})
        columns.append(
            {'name': _("Primary Sanitation".upper()),
             'bit': '{{object.survey.toilet_type}}'})
        columns.append(
            {'name': _("Shared?".upper()),
             'bit': '{{object.survey.share}}'})
        columns.append(
            {'name': _("Primary source of water".upper()),
             'bit': '{{object.survey.water_source}}'})
        columns.append(
            {'name': _("Treatment Method ".upper()),
             'bit': '{{object.survey.treat_method}}'})

        sub_columns = None
        return columns, sub_columns

    @classmethod
    def bednet_summary_minimal(cls):
        columns = []
        columns.append(
            {'name': _("HH".upper()),
            'bit': '{{object.household.health_id.upper}}'})
        columns.append(
            {'name': cls._meta.get_field('location').verbose_name.upper(), \
             'bit': '{{ object.location }}'})
        columns.append(
            {'name': _("HH Name".upper()), \
             'bit': '{{ object.first_name }} {{ object.last_name }}'})
        columns.append(
            {'name': _("# SSs".upper()),
             'bit': '{{object.survey.num_site}}'})
        columns.append(
            {'name': _("# Func. Nets".upper()),
             'bit': '{{object.survey.function}}'})
        columns.append(
            {'name': _("# Elr. Nets".upper()),
             'bit': '{{object.survey.earlier}}'})
        columns.append(
            {'name': _("# Dmgd. Nets".upper()),
             'bit': '{{object.survey.damaged}}'})
        columns.append(
            {'name': _("# Rqrd. Nets".upper()),
             'bit': '{{object.required_bednet}}'})
        columns.append(
            {'name': _("# U5 LN".upper()),
             'bit': '{{object.survey.under_five}}'})
        columns.append(
            {'name': _("# Slept on Net".upper()),
             'bit': '{{object.survey.slept_bednet}}'})
        columns.append(
            {'name': _("# Hanging Nets".upper()),
             'bit': '{{object.survey.hanging}}'})
        columns.append(
            {'name': _("Reason".upper()),
             'bit': '{{object.survey.reason}}'})
        columns.append(
            {'name': _("Primary SAN".upper()),
             'bit': '{{object.survey.toilet_type}}'})
        columns.append(
            {'name': _("Shared?".upper()),
             'bit': '{{object.survey.share}}'})
        columns.append(
            {'name': _("P. Water Source".upper()),
             'bit': '{{object.survey.water_source}}'})
        columns.append(
            {'name': _("Treatment".upper()),
             'bit': '{{object.survey.treat_method}}'})

        sub_columns = None
        return columns, sub_columns

class TheCHWReport(CHW):
    class Meta:
        verbose_name = _("Community Health Worker Report")
        proxy = True

    @property
    def mobile_phone(self):
        return self.connection().identity

    @property
    def num_of_patients(self):
        num = Patient.objects.filter(chw=self, \
                            status=Patient.STATUS_ACTIVE).count()
        return num

    @property
    def num_of_underfive(self):
        return self.patients_under_five().count()

    def patients_under_five(self, today = date.today()):
        sixtym = today - timedelta(int(30.4375 * 59))
        return Patient.objects.filter(chw=self, dob__gte=sixtym, \
                            status=Patient.STATUS_ACTIVE)

    @property
    def num_of_under_nine(self):
        return self.patients_under_nine().count()

    def patients_under_nine(self):
        ninem = date.today() - timedelta(int(30.4375 * 9))
        return Patient.objects.filter(chw=self, dob__gte=ninem, \
                            status=Patient.STATUS_ACTIVE)

    @property
    def num_of_sam(self):
        num = NutritionReport.objects.filter(created_by=self, \
                            status=NutritionReport.STATUS_SEVERE_COMP).count()
        num += NutritionReport.objects.filter(created_by=self, \
                                status=NutritionReport.STATUS_SEVERE).count()
        return num

    @property
    def num_of_mam(self):
        num = NutritionReport.objects.filter(created_by=self, \
                            encounter__patient__status=Patient.STATUS_ACTIVE, \
                                status=NutritionReport.STATUS_MODERATE).count()
        return num

    def mam_cases(self, startDate=None, endDate=None):
        return NutritionReport.objects.filter(encounter__chw=self, \
                            encounter__patient__status=Patient.STATUS_ACTIVE, \
                                encounter__encounter_date__gte=startDate, \
                                encounter__encounter_date__lte=endDate).count()

    def severe_mam_cases(self, startDate=None, endDate=None):
        num = NutritionReport.objects.filter(encounter__chw=self, \
                            encounter__patient__status=Patient.STATUS_ACTIVE, \
                            status=NutritionReport.STATUS_SEVERE_COMP, \
                            encounter__encounter_date__gte=startDate, \
                            encounter__encounter_date__lte=endDate).count()
        num += NutritionReport.objects.filter(encounter__chw=self, \
                            encounter__patient__status=Patient.STATUS_ACTIVE, \
                                status=NutritionReport.STATUS_SEVERE, \
                            encounter__encounter_date__gte=startDate, \
                            encounter__encounter_date__lte=endDate).count()
        return num

    @property
    def num_of_healthy(self):
        num = NutritionReport.objects.filter(created_by=self, \
                            encounter__patient__status=Patient.STATUS_ACTIVE, \
                                status=NutritionReport.STATUS_HEALTHY).count()
        return num

    @property
    def num_of_visits(self):
        num = HouseholdVisitReport.objects.filter(created_by=self).count()
        return num

    def two_weeks_visits(self):
        two_weeks = datetime.now() + \
            relativedelta(weekday=calendar.MONDAY, days=-13)
        two_weeks = datetime.combine(two_weeks.date(), time(0, 0))
        return HouseholdVisitReport.objects.filter(encounter__chw=self, \
                            encounter__encounter_date__gte=two_weeks)\
                            .count()

    @property
    def num_muac_eligible(self):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        sixm = date.today() - timedelta(int(30.4375 * 6))
        num = Patient.objects.filter(chw=self, dob__gte=sixtym, \
                                    status=Patient.STATUS_ACTIVE, \
                                    dob__lte=sixm).count()
        return num

    @classmethod
    def total_muac_eligible(cls):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        sixm = date.today() - timedelta(int(30.4375 * 6))
        num = Patient.objects.filter(dob__gte=sixtym, \
                                    status=Patient.STATUS_ACTIVE, \
                                     dob__lte=sixm).count()
        return num

    @property
    def num_of_sms(self):
        identity = self.connection().identity
        num = LoggedMessage.incoming.filter(identity=identity).count()
        return num

    @property
    def number_of_households(self, today=None):
        return self.households(today).count()

    def households(self, today=None):
        '''
        List of households belonging to this CHW
        '''
        p = Patient.objects.filter(health_id=F('household__health_id'), \
                                        chw=self, status=Patient.STATUS_ACTIVE)
        if today is None:
            return p
        else:
            return p.filter(created_on__lte=today)

    def muac_list(self):
        '''
        List of patients in the muac age bracket
            - 6 months >= patient.age < 60 months
        '''
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        sixm = date.today() - timedelta(int(30.4375 * 6))
        patients = ThePatient.objects.filter(chw=self, dob__gte=sixtym, \
                                     dob__lte=sixm, \
                                     status=Patient.STATUS_ACTIVE)
        return patients

    def num_of_householdvisits(self):
        return HouseholdVisitReport.objects.filter(encounter__chw=self).count()

    def household_visit(self, startDate=None, endDate=None):
        return HouseholdVisitReport.objects.filter(encounter__chw=self, \
                                encounter__encounter_date__gte=startDate, \
                                encounter__encounter_date__lte=endDate).count()

    def household_visits_for_month(self, offset=0):
        # This list comprehension deserves some explanation.
        # First, we get a list of days from 30+offset days ago up
        # to today.
        # Then, we get (day, count) tuples for each of those
        # days, where count contains the number of
        # HH visits for that day by this CHW
        return [(i, self.household_visit(date.today() + timedelta(i), \
            date.today() + timedelta(i+1))) \
                for i in xrange(-30-offset,-offset)]

    def percentage_ontime_visits(self):
        households = self.households()
        num_on_time = 0
        for household in households:
            thepatient = ThePatient.objects.get(health_id=household.health_id)
            if thepatient.visit_within_90_days_of_last_visit():
                num_on_time += 1
        if households.count() == 0:
            return None
        if num_on_time is 0:
            return 0
        else:
            total_households = households.count()
            return int(round((num_on_time / float(total_households)) * 100))

    def num_of_births(self):
        return BirthReport.objects.filter(encounter__chw=self).count()

    def percentage_ontime_birth_visits(self):
        births = BirthReport.objects.filter(encounter__chw=self)
        count = 0
        for birth in births:
            thepatient = ThePatient.objects.get(id=birth.encounter.patient)
            if thepatient.check_visit_within_seven_days_of_birth():
                count += 1
        if births.count() == 0:
            return None
        elif not count:
            return count
        else:
            return int(round(100 * (count / float(births.count()))))

    def num_of_clinic_delivery(self):
        return BirthReport.objects.filter(encounter__chw=self, \
                    clinic_delivery=BirthReport.CLINIC_DELIVERY_YES).count()

    def percentage_clinic_deliveries(self):
        num_of_clinic_delivery = self.num_of_clinic_delivery()
        num_of_births = self.num_of_births()
        if num_of_births == 0:
            return None
        else:
            return int(round(num_of_clinic_delivery / float(num_of_births)) * 100)

    def num_underfive_refferred(self):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        rr = ReferralReport.objects.filter(encounter__patient__dob__lte=sixtym,
                        encounter__chw=self)
        return rr.count()

    def num_underfive_malaria(self):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        fr = FeverReport.objects.filter(encounter__patient__dob__lte=sixtym, \
                                        encounter__chw=self)
        return fr.count()

    def rdt_cases(self, startDate=None, endDate=None):
        return FeverReport.objects.filter(encounter__chw=self, \
                                encounter__encounter_date__gte=startDate, \
                                encounter__encounter_date__lte=endDate).count()

    def num_underfive_diarrhea(self):
        #TODO
        return 0

    def percentage_ontime_muac(self):
        underfives = self.patients_under_five()
        if underfives.count() == 0:
            return None

        count = 0
        for achild in underfives:
            thepatient = ThePatient.objects.get(id=achild.id)
            if thepatient.ontime_muac():
                count += 1
            return 

        if not count:
            return count
        else:
            total_count = underfives.count()
            return int(round(100 * (count / float(total_count))))

    def num_of_active_sam_cases(self, today=date.today()):
        count = 0
        danger = (NutritionReport.STATUS_SEVERE, \
                        NutritionReport.STATUS_SEVERE_COMP)
        nr = NutritionReport.objects\
                        .filter(encounter__chw=self, status__in=danger,\
                        encounter__encounter_date__lte=today)\
                        .values('encounter__patient').distinct()
        for r in nr:
            p = Patient.objects.get(id=r['encounter__patient'])
            latest = NutritionReport\
                .objects\
                .filter(encounter__patient=p,\
                    encounter__encounter_date__lte=today)\
                .latest()
            if latest.status in danger:
                count += 1
        return count

    def num_of_pregnant_women(self):
        return len(self.pregnant_women())

    def pregnant_women(self, today=datetime.now()):
        c = []
        pregs = PregnancyReport\
            .objects\
            .filter(encounter__chw=self,\
                encounter__encounter_date__lte=today)\
            .values('encounter__patient')\
            .distinct()

        for preg in pregs:
            patient = Patient.objects.get(id=preg['encounter__patient'])
            pr = PregnancyReport\
                .objects\
                .filter(encounter__patient=patient,
                    encounter__encounter_date__lte=today)\
                .latest()
            days = (pr.encounter.encounter_date - today).days
            months = round(days / 30.4375)
            if pr.pregnancy_month + months < 9:
                c.append(patient)
        return c

    def num_pregnant_refferred(self):
        pwomen = self.pregnant_women()
        rr = ReferralReport.objects.filter(encounter__patient__in=pwomen, \
                                        encounter__chw=self)
        return rr.count()

    def percentage_pregnant_ontime_visits(self):
        pwomen = self.pregnant_women()
        if len(pwomen) == 0:
            return None

        count = 0
        for patient in pwomen:
            pr = PregnancyReport.objects.filter(encounter__patient=patient)\
                                        .latest()
            latest_date = pr.encounter.encounter_date
            old_date = latest_date - timedelta(6 * 7)
            pr = PregnancyReport.objects.filter(encounter__patient=patient, \
                                encounter__encounter_date__gte=old_date, \
                                encounter__encounter_date__lt=latest_date)
            if pr.count():
                count += 1
        if not count:
            return count
        else:
            total_count = len(pwomen)
            return int(round(100 * (count / float(total_count))))

    def percentage_ontime_followup(self):
        referrals = ReferralReport.objects.filter(encounter__chw=self)
        if not referrals:
            return None
        num_referrals = referrals.count()
        if num_referrals == 0:
            return None

        ontimefollowup = 0
        for referral in referrals:
            rdate = referral.encounter.encounter_date
            day2later = day_end(rdate + timedelta(2))
            fur = FollowUpReport.objects.filter(encounter__chw=self, \
                            encounter__patient=referral.encounter.patient, \
                            encounter__encounter_date__gt=rdate, \
                            encounter__encounter_date__lte=day2later)
            if fur:
                ontimefollowup += 1
        return '%s' % int(round((ontimefollowup / \
                        float(num_referrals)) * 100))

    def median_number_of_followup_days(self):
        referrals = ReferralReport.objects.filter(encounter__chw=self)
        lsdays = []
        for referral in referrals:
            rdate = referral.encounter.encounter_date
            fur = FollowUpReport.objects.filter(encounter__chw=self, \
                            encounter__patient=referral.encounter.patient, \
                            encounter__encounter_date__gt=rdate)\
                            .order_by('encounter__encounter_date')
            if fur:
                fdate = fur[0].encounter.encounter_date
                lsdays.append((fdate - rdate).days)
        if not lsdays:
            return ''
        return int(get_median(lsdays))

    def sms_error_rate(self):
        total_sms = LoggedMessage.incoming.filter(identity=self.connection()\
                                    .identity).count()
        if total_sms == 0:
            return None
        total_error_sms = LoggedMessage.outgoing.filter(identity=self\
                                    .connection().identity, \
                                    text__icontains='error').count()
        return int(round((total_error_sms / float(total_sms)) * 100))

    def days_since_last_sms(self):
        now = datetime.now()
        last_sms = LoggedMessage.incoming.filter(identity=self.connection()\
                                    .identity, date__lte=now)\
                                    .order_by('-date')
        if not last_sms:
            return None
        return (now - last_sms[0].date).days

    def activity_summary(self):
        today = datetime.today()
        startDate = today - timedelta(today.weekday())
        p = {}

        p['sdate'] = startDate.strftime('%d %b')
        p['edate'] = today.strftime('%d %b')
        p['severemuac'] = self.severe_mam_cases(startDate=startDate, \
                            endDate=today)
        p['numhvisit'] = self.household_visit(startDate=startDate, \
                            endDate=today)
        p['muac'] = self.mam_cases(startDate=startDate, endDate=today)
        p['rdt'] = self.rdt_cases(startDate=startDate, endDate=today)
        p['household'] = self.number_of_households
        p['tclient'] = self.num_of_patients
        p['ufive'] = self.num_of_underfive
        p['unine'] = self.num_of_under_nine

        return p

    def chw_activities_summary(self, startDate, endDate=datetime.today()):
        p = {}

        p['sdate'] = startDate.strftime('%d %b')
        p['edate'] = endDate.strftime('%d %b')
        p['severemuac'] = self.severe_mam_cases(startDate=startDate, \
                            endDate=endDate)
        p['numhvisit'] = self.household_visit(startDate=startDate, \
                            endDate=endDate)
        p['muac'] = self.mam_cases(startDate=startDate, endDate=endDate)
        p['rdt'] = self.rdt_cases(startDate=startDate, endDate=endDate)
        p['household'] = self.number_of_households
        p['tclient'] = self.num_of_patients
        p['ufive'] = self.num_of_underfive
        p['unine'] = self.num_of_under_nine

        return p

    def num_of_bednetsurvey(self):
        return BedNetReport.objects.filter(encounter__chw=self).count()

    def per_bednetsurvey(self):
        #Percentage survey done
        num_survey = self.num_of_bednetsurvey()
        num_household = self.number_of_households
        if num_household > 0:
            ans = int(round((num_survey / float(num_household)) * 100))
        else:
            ans = 0
        return ans

    def bednet_survey(self):
        #Get aggregate of bednets survey questions per chw
        survey = BedNetReport.objects.filter(encounter__chw=self)\
                                     .aggregate(\
                                            total=Count('encounter'),
                                            damaged=Sum('damaged_nets'),
                                            function=Sum('function_nets'),
                                            num_site=Sum('sleeping_sites'),
                                            earlier=Sum('earlier_nets'))
        for item in survey:
            if survey[item] is None:
                survey[item] = '-'
        return survey

    def required_bednet(self):
        total = self.num_sleepingsite() - self.num_funcbednet()
        return total

    def num_sanitation(self):
        'total survey done  on sanitation'
        return SanitationReport.objects.filter(encounter__chw=self).count()

    def num_netutilization(self):
        'total survey done on bednet utilization'
        return BednetUtilization.objects.filter(encounter__chw=self).count()

    def num_drinkingwater(self):
        'total survey done on drinking water '
        return DrinkingWaterReport.objects.filter(encounter__chw=self).count()

    @classmethod
    def muac_summary(cls):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        sixm = date.today() - timedelta(int(30.4375 * 6))
        order = '-encounter__encounter_date'
        muac = NutritionReport.objects.filter(\
                                        encounter__patient__dob__gte=sixtym,
                                        encounter__patient__dob__lte=sixm)\
                                        .order_by(order)\
                                        .values('encounter__patient')\
                                        .distinct()

        num_healthy = muac.filter(\
                        status=NutritionReport.STATUS_HEALTHY).count()
        num_mam = muac.filter(\
                        status=NutritionReport.STATUS_MODERATE).count()
        num_sam = muac.filter(\
                        status=NutritionReport.STATUS_SEVERE).count()
        num_comp = muac.filter(\
                        status=NutritionReport.STATUS_SEVERE_COMP).count()
        num_eligible = TheCHWReport.total_muac_eligible()

        unkwn = num_eligible - num_healthy - num_mam - num_sam - num_comp
        if num_eligible > 0:
            hp = int(round((num_healthy / float(num_eligible)) * 100))
            modp = int(round((num_mam / float(num_eligible)) * 100))
            svp = int(round((num_sam / float(num_eligible)) * 100))
            svcomp = int(round((num_comp / float(num_eligible)) * 100))
            unkp = int(round((unkwn / float(num_eligible)) * 100))
        else:
            hp = modp = svp = svcomp = unkp = 0

        info = _(u"[%(hel)d, %(mmod)d, %(sev)d, %(sevcomp)d, %(unkwn)d], {" \
                        "legend: [\"%(hp)d%% Healthy\", \"%(mp)d%% " \
                        "Moderate\",\"%(svp)d%% Severe\", " \
                        "\"%(scm)d%% Severe Completely\", " \
                        "\"%(unkp)d%% Unknown\"]") % \
                        {'hel': num_healthy, 'mmod': num_mam, 'sev': num_sam, \
                            'sevcomp': num_comp, 'unkwn': unkwn, 'hp': hp, \
                            'mp': modp, 'svp': svp, 'scm': svcomp, \
                            'unkp': unkp}
        return info

    @classmethod
    def total_at_risk(cls):
        num = NutritionReport.objects.filter(\
                                status__in=(NutritionReport.STATUS_SEVERE, \
                                NutritionReport.STATUS_SEVERE_COMP, \
                                NutritionReport.STATUS_MODERATE)).count()
        return num

    @classmethod
    def summary(cls):
        columns = []
        columns.append(
            {'name': cls._meta.get_field('alias').verbose_name.upper(), \
             'bit': '@{{ object.alias }}'})
        columns.append(
            {'name': _("Name".upper()), \
             'bit': '{{ object.first_name }} {{ object.last_name }}'})
        columns.append(
            {'name': cls._meta.get_field('location').verbose_name.upper(), \
             'bit': '{{ object.location }}'})
        columns.append(
            {'name': "No. of Patients".upper(), \
             'bit': '{{ object.num_of_patients }}'})
        columns.append(
            {'name': "No. Under 5".upper(), \
             'bit': '{{ object.num_of_underfive }}'})
        columns.append(
            {'name': "No. of Visits".upper(), \
             'bit': '{{ object.num_of_visits }}'})
        columns.append(
            {'name': "No. SAM".upper(), \
             'bit': '{{ object.num_of_sam }}'})
        columns.append(
            {'name': "No. MAM".upper(), \
             'bit': '{{ object.num_of_mam }}'})
        columns.append(
            {'name': "No. HEALTHY".upper(), \
             'bit': '{{ object.num_of_healthy }}'})
        columns.append(
            {'name': "No. SMS Sent".upper(), \
             'bit': '{{ object.num_of_sms }}'})

        sub_columns = None
        return columns, sub_columns

    @classmethod
    def chw_bednet_summary(cls):
        columns = []
        columns.append(
            {'name': cls._meta.get_field('location').verbose_name.upper(), \
             'bit': '{{object.location }}'})
        columns.append(
            {'name': _("Name".upper()), \
             'bit': '{{object.first_name }} {{ object.last_name }}'})
        columns.append(
            {'name': "No. of House holds".upper(), \
             'bit': '{{object.number_of_households}}'})
        columns.append(
            {'name': "Household Survey Done".upper(), \
             'bit': '{{object.bednet_survey.total}}'})
        columns.append(
            {'name': "Percentage".upper(), \
             'bit': '{{object.per_bednetsurvey}}'})
        columns.append(
            {'name': "Total Sleeping site".upper(), \
             'bit': '{{object.bednet_survey.num_site}}'})
        columns.append(
            {'name': "Functioning Bednet".upper(), \
             'bit': '{{ object.bednet_survey.function}}'})
        columns.append(
            {'name': "Damaged Bednet".upper(), \
             'bit': '{{object.bednet_survey.damaged}}'})
        columns.append(
            {'name': "Earlier(b4 2009)".upper(), \
             'bit': '{{object.bednet_survey.earlier}}'})
        columns.append(
            {'name': "Required Bednet".upper(), \
             'bit': '{{object.required_bednet}}'})
        columns.append(
            {'name': "Bednet Utilization".upper(), \
             'bit': '{{object.num_netutilization}}'})
        columns.append(
            {'name': "#Sanitation ".upper(), \
             'bit': '{{object.num_sanitation}}'})
        columns.append(
            {'name': "#Drinking water ".upper(), \
             'bit': '{{object.num_drinkingwater}}'})

        sub_columns = None
        return columns, sub_columns

    @classmethod
    def sms_per_day(cls):
        days_of_the_week = seven_days_to_date()
        data = []
        for day in days_of_the_week:
            start = day_start(day['date'])
            end = day_end(day['date'])
            num = LoggedMessage.incoming.filter(date__gte=start, \
                                           date__lte=end).count()
            total_error_sms = LoggedMessage.outgoing.filter(date__gte=start, \
                                           date__lte=end, \
                                    text__icontains='error').count()
            csms = num - total_error_sms

            hvr = HouseholdVisitReport.objects.filter(\
                            encounter__encounter_date__gt=start, \
                            encounter__encounter_date__lte=end).count()
            fr = FeverReport.objects.filter(\
                            encounter__encounter_date__gt=start, \
                            encounter__encounter_date__lte=end).count()
            nutr = NutritionReport.objects.filter(\
                            encounter__encounter_date__gt=start, \
                            encounter__encounter_date__lte=end).count()

            data.append({'day': day["day"], 'total': num, \
                         'correcct_sm': csms, 'wrong_sms': total_error_sms, \
                         'muac': nutr, 'rdt': fr, 'householdv': hvr})
        return data


class OperationalReport():
    columns = []

    def __init__(self):
        columns = []
        columns.append({ \
            'name': _("CHW"),
            'abbr': _("CHW"),
            'bit': '{{object}}'})
        columns.append({ \
            'name': _("# of Households"), \
            'abbr': _("#HH"), \
            'bit': '{{object.number_of_households}}'})
        columns.append({ \
            'name': _("# of Household Visits"), \
            'abbr': _("#HH-V"), \
            'bit': '{{object.num_of_householdvisits}}'})
        columns.append({
            'name': _("% of HHs receiving on-time routine visit "\
                                    "(within 90 days) [S23]"), \
            'abbr': _("%OTV"), \
            'bit': '{% if object.percentage_ontime_visits %}' \
                   '{{ object.percentage_ontime_visits }}%'\
                   '{% else %}-{% endif %}'})
        columns.append({ \
            'name': _("# of Births"), \
            'abbr': _('#Bir'), \
            'bit': '{{object.num_of_births}}'})
        columns.append({ \
            'name': _("% Births delivered in "\
                                "Health Facility [S4]"),
            'abbr': _('%BHF'), \
            'bit': '{% if object.percentage_clinic_deliveries %}' \
                   '{{ object.percentage_clinic_deliveries }}%'\
                   '{% else %}-{% endif %}'})
        columns.append({ \
            'name': _("% Newborns checked within 7 days of birth "\
                            "[S6]"), \
            'abbr': _('%NNV'), \
            'bit': '{% if object.percentage_ontime_birth_visits %}' \
                   '{{ object.percentage_ontime_birth_visits }}%'\
                   '{% else %}-{% endif %}'})
        columns.append({ \
            'name': _("# of Under-5s"), \
            'abbr': _('#U5'), \
            'bit': '{{object.num_of_underfive}}'})
        columns.append({
            'name': _("# Under-5 Referred for Danger Signs"), \
            'abbr': _('#U5-DS'), \
            'bit': '{{object.num_underfive_refferred}}'})
        columns.append({ \
            'name': _("# Under-5 Treated for Malarias"), \
            'abbr': _('#U5-Mal'), \
            'bit': '{{object.num_underfive_malaria}}'})
        columns.append({ \
            'name': _("# Under-5 Treated for Diarrhea"), \
            'abbr': _('#U5-Dia'), \
            'bit': '{{object.num_underfive_diarrhea}}'})
        columns.append({ \
            'name': _("% Under-5 receiving on-time MUAC "\
                                    "(within 90 days) [S11]"), \
            'abbr': _('#U5-MUAC'), \
            'bit': '{% if object.percentage_ontime_muac %}' \
                   '{{ object.percentage_ontime_muac }}%'\
                   '{% else %}-{% endif %}'})
        columns.append({ \
            'name': _("# of Active SAM cases"), \
            'abbr': _('#U5-SAM'), \
            'bit': '{{object.num_of_active_sam_cases}}'})
        columns.append({ \
            'name': _("# of Pregnant Women"), \
            'abbr': _('#PW'), \
            'bit': '{{object.num_of_pregnant_women}}'})
        columns.append({ \
            'name': _("# Pregnant Women Referred for "\
                                    "Danger Signs"),
            'abbr': _('#PW-DS'), \
            'bit': '{{object.num_pregnant_refferred}}'})
        columns.append({ \
            'name': _("% Pregnant receiving on-time visit"\
                        " (within 6 weeks) [S24]"), \
            'abbr': _('%PW-OTV'), \
            'bit': '{% if object.percentage_pregnant_ontime_visits %}' \
                   '{{ object.percentage_pregnant_ontime_visits }}%'\
                   '{% else %}-{% endif %}'})
        columns.append({ \
            'name': _("% Referred / Treated receiving on-time "\
                            "follow-up (within 2 days) [S13]"),
            'abbr': _('%Ref'), \
            'bit': '{% if object.percentage_ontime_followup %}' \
                   '{{ object.percentage_ontime_followup }}%'\
                   '{% else %}-{% endif %}'})
        columns.append({ \
            'name': _("Median # of days for follow-up [S25]"), \
            'abbr': _('#Fol'), \
            'bit': '{{object.median_number_of_followup_days}}'})
        columns.append({ \
            'name': _("SMS Error Rate %"), \
            'abbr': _('%Err'), \
            'bit': '{% if object.sms_error_rate %}' \
                   '{{ object.sms_error_rate }}%'\
                   '{% else %}-{% endif %}'})
        columns.append({ \
            'name': _("Days since last SMS transmission"), \
            'abbr': _('#Days'), \
            'bit': '{{object.days_since_last_sms}}'})
        self.columns = columns

    def get_columns(self):
        return self.columns


class ClinicReport(Clinic):

    class Meta:
        verbose_name = _("Clinic Report")
        proxy = True

    @property
    def registeredpatient(self):
        total = Patient.objects.filter(chw__location=self)
        return total.count()

    @property
    def househoulds(self):
        thousehold = Patient.objects.filter(health_id=F(\
                                                    'household__health_id'),\
                                        chw__location=self)
        return thousehold.count()

    @property
    def pntied_household(self):
        nttied_household = Patient.objects.filter(chw__location=self,\
                                            household__health_id='xxxxx')
        return nttied_household.count()

    @property
    def rdtreported(self):
        fr = FeverReport.objects.filter(encounter__patient__chw__location=self)
        return fr.count()

    @property
    def hvisit(self):
        hvisit = HouseholdVisitReport.objects.filter(\
                                    encounter__patient__chw__location=self)
        return hvisit.count()

    @property
    def muacreport(self):
        muac = NutritionReport.objects.filter(\
                                    encounter__patient__chw__location=self)
        return muac.count()

    def monthly_summary(self, month=None, year=None):
        if not month:
            month = datetime.today().month
        if not year:
            year = datetime.today().year
        onfirst = datetime(year=year, month=month, day=1)
        rdt = FeverReport.objects.filter(encounter__patient__clinic=self, \
                                    encounter__encounter_date__month=month, \
                                    encounter__encounter_date__year=year)\
                                .count()
        prdt = FeverReport.objects.filter(encounter__patient__clinic=self, \
                                    encounter__encounter_date__month=month, \
                                    encounter__encounter_date__year=year, \
                                    rdt_result=FeverReport.RDT_POSITIVE)\
                                .count()

        nut = NutritionReport.objects.filter(encounter__patient__clinic=self, \
                                    encounter__encounter_date__month=month, \
                                    encounter__encounter_date__year=year)\
                                .count()
        snut = NutritionReport.objects.filter(encounter__patient__clinic=self,\
                                encounter__encounter_date__month=month, \
                                encounter__encounter_date__year=year, \
                                status__in=(NutritionReport.STATUS_SEVERE, \
                                NutritionReport.STATUS_SEVERE_COMP, \
                                NutritionReport.STATUS_MODERATE))\
                                .count()
        return {'clinic': self,
                'month': onfirst.strftime("%B"),
                'rdt': rdt,
                'positive_rdt': prdt,
                'nutrition': nut,
                'malnutrition': snut}

    @classmethod
    def summary(cls):
        columns = []
        columns.append(
            {'name': cls._meta.get_field('name').verbose_name.upper(), \
             'bit': '{{object.name}}'})
        columns.append(
            {'name': _("# of Household".upper()), \
             'bit': '{{object.househoulds}}'})
        columns.append(
            {'name': _("#House visits".upper()), \
             'bit': '{{object.hvisit}}'})
        columns.append(
            {'name': _("#Patients".upper()), \
             'bit': '{{object.registeredpatient}}'})
        columns.append(
            {'name': _("#MUAC".upper()), \
             'bit': '{{object.muacreport}}'})
        columns.append(
            {'name': "#RDT ".upper(), \
             'bit': '{{object.rdtreported}}'})

        sub_columns = None
        return columns, sub_columns


class SummaryReport():

    '''Cluster-wide Summary Reports'''

    def num_of_patients(self):
        return Patient.objects.all().count()

    def num_of_underfive(self):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        return Patient.objects.filter(dob__gte=sixtym).count()

    def num_of_households(self):
        return Patient.objects\
                    .filter(health_id=F('household__health_id')).count()

    def num_pregnant(self):
        c = 0
        pregs = PregnancyReport.objects.filter()\
                                .values('encounter__patient').distinct()
        for preg in pregs:
            patient = Patient.objects.get(id=preg['encounter__patient'])
            pr = PregnancyReport.objects.filter(encounter__patient=patient)\
                                        .latest()
            days = (pr.encounter.encounter_date - datetime.now()).days
            months = round(days / 30.4375)
            if pr.pregnancy_month + months < 9:
                c += 1
        return c

    @classmethod
    def summary(cls):
        sr = cls()
        return {"summary": {"num_underfive": sr.num_of_underfive(), \
                            "num_patients": sr.num_of_patients(), \
                            "num_households": sr.num_of_households(), \
                            "num_pregnant": sr.num_pregnant()}}


class WeekSummaryReport():

    '''This week Summary Reports'''
    def num_of_patients(self, startDate=None, endDate=None):
        return Patient.objects.filter(created_on__gte=startDate, \
                                      created_on__lte=endDate).count()

    def num_of_underfive(self, startDate=None, endDate=None):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        return Patient.objects.filter(dob__gte=sixtym, \
                                      created_on__gte=startDate, \
                                      created_on__lte=endDate).count()

    def num_of_households(self, startDate=None, endDate=None):
        return Patient.objects\
                    .filter(health_id=F('household__health_id')).count()

    def num_of_muac(self, startDate=None, endDate=None):
        num = NutritionReport.objects.filter(\
                            status=NutritionReport.STATUS_SEVERE_COMP, \
                            encounter__encounter_date__gte=startDate, \
                            encounter__encounter_date__lte=endDate).count()
        num += NutritionReport.objects.filter(\
                                status=NutritionReport.STATUS_SEVERE, \
                            encounter__encounter_date__gte=startDate, \
                            encounter__encounter_date__lte=endDate).count()

        return num

    def num_of_rdts(self, startDate=None, endDate=None):
        return FeverReport.objects.filter(\
                                encounter__encounter_date__gte=startDate, \
                                encounter__encounter_date__lte=endDate).count()

    def num_pregnant(self, startDate=None, endDate=None):
        c = 0
        pregs = PregnancyReport.objects.filter(\
                                encounter__encounter_date__gte=startDate, \
                                encounter__encounter_date__lte=endDate)\
                                .values('encounter__patient').distinct()
        for preg in pregs:
            patient = Patient.objects.get(id=preg['encounter__patient'])
            pr = PregnancyReport.objects.filter(encounter__patient=patient)\
                                        .latest()
            days = (pr.encounter.encounter_date - datetime.now()).days
            months = round(days / 30.4375)
            if pr.pregnancy_month + months < 9:
                c += 1
        return c

    @classmethod
    def savgummary(cls):
        sr = cls()
        endDate = datetime.today()
        startDate = endDate - timedelta(endDate.weekday())

        return {"week_report": {"num_mam_sam": sr.num_of_muac(\
                                    startDate=startDate, endDate=endDate), \
                            "num_rdt": sr.num_of_rdts( \
                                    startDate=startDate, endDate=endDate), \
                            "num_pregnant": sr.num_pregnant( \
                                    startDate=startDate, endDate=endDate)}}


class MonthSummaryReport():

    '''This month Summary Reports'''
    def num_of_patients(self, startDate=None, endDate=None):
        return Patient.objects.filter(created_on__gte=startDate, \
                                      created_on__lte=endDate).count()

    def num_of_underfive(self, startDate=None, endDate=None):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        return Patient.objects.filter(dob__gte=sixtym, \
                                      created_on__gte=startDate, \
                                      created_on__lte=endDate).count()

    def num_of_households(self, startDate=None, endDate=None):
        return Patient.objects\
                    .filter(health_id=F('household__health_id')).count()

    def num_of_muac(self, startDate=None, endDate=None):
        num = NutritionReport.objects.filter(\
                            status=NutritionReport.STATUS_SEVERE_COMP, \
                            encounter__encounter_date__gte=startDate, \
                            encounter__encounter_date__lte=endDate).count()
        num += NutritionReport.objects.filter(\
                                status=NutritionReport.STATUS_SEVERE, \
                            encounter__encounter_date__gte=startDate, \
                            encounter__encounter_date__lte=endDate).count()

        return num

    def num_of_rdts(self, startDate=None, endDate=None):
        return FeverReport.objects.filter(\
                                encounter__encounter_date__gte=startDate, \
                                encounter__encounter_date__lte=endDate).count()

    def num_pregnant(self, startDate=None, endDate=None):
        c = 0
        pregs = PregnancyReport.objects.filter(\
                                encounter__encounter_date__gte=startDate, \
                                encounter__encounter_date__lte=endDate)\
                                .values('encounter__patient').distinct()
        for preg in pregs:
            patient = Patient.objects.get(id=preg['encounter__patient'])
            pr = PregnancyReport.objects.filter(encounter__patient=patient)\
                                        .latest()
            days = (pr.encounter.encounter_date - datetime.now()).days
            months = round(days / 30.4375)
            if pr.pregnancy_month + months < 9:
                c += 1
        return c

    @classmethod
    def summary(cls):
        sr = cls()
        endDate = last_day_of_month(datetime.today())
        startDate = first_day_of_month(datetime.today())

        return {"month_report": {"num_mam_sam": sr.num_of_muac(\
                                    startDate=startDate, endDate=endDate), \
                            "num_rdt": sr.num_of_rdts( \
                                    startDate=startDate, endDate=endDate), \
                            "num_pregnant": sr.num_pregnant( \
                                    startDate=startDate, endDate=endDate)}}


class GeneralSummaryReport():

    '''This month Summary Reports'''
    def num_of_patients(self, startDate=None, endDate=None):
        return Patient.objects.filter().count()

    def num_of_underfive(self, startDate=None, endDate=None):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        return Patient.objects.filter(dob__gte=sixtym).count()

    def num_of_households(self, startDate=None, endDate=None):
        return Patient.objects\
                    .filter(health_id=F('household__health_id')).count()

    def num_of_muac(self, startDate=None, endDate=None):
        num = NutritionReport.objects.filter(\
                            status=NutritionReport.STATUS_SEVERE_COMP).count()
        num += NutritionReport.objects.filter(\
                                status=NutritionReport.STATUS_SEVERE).count()

        return num

    def num_of_rdts(self, startDate=None, endDate=None):
        return FeverReport.objects.filter().count()

    def num_pregnant(self, startDate=None, endDate=None):
        c = 0
        pregs = PregnancyReport.objects.filter()\
                                .values('encounter__patient').distinct()
        for preg in pregs:
            patient = Patient.objects.get(id=preg['encounter__patient'])
            pr = PregnancyReport.objects.filter(encounter__patient=patient)\
                                        .latest()
            days = (pr.encounter.encounter_date - datetime.now()).days
            months = round(days / 30.4375)
            if pr.pregnancy_month + months < 9:
                c += 1
        return c

    @classmethod
    def summary(cls):
        sr = cls()
        endDate = last_day_of_month(datetime.today())
        startDate = first_day_of_month(datetime.today())

        return {"general_summary_report": {"num_mam_sam": sr.num_of_muac(\
                                    startDate=startDate, endDate=endDate), \
                            "num_rdt": sr.num_of_rdts( \
                                    startDate=startDate, endDate=endDate), \
                            "num_pregnant": sr.num_pregnant( \
                                    startDate=startDate, endDate=endDate)}}


class TheBHSurveyReport(TheCHWReport):
    '''
    The Bednet Household Healthy Survey Report
    '''
    class Meta:
        verbose_name = _(u"The Bednet Household Healthy Survey Report")
        proxy = True

    def bednet_aggregates(self):
        data = BedNetReport.objects.filter(encounter__chw=self)\
                                    .aggregate(Avg('sleeping_sites'),
                                    Count('encounter'),
                                    Sum('sleeping_sites'),
                                    Sum('function_nets'),
                                    Sum('earlier_nets'),
                                    Sum('damaged_nets'))
        bednet_util = BednetUtilization.objects.filter(encounter__chw=self)\
                                                .aggregate(Count('encounter'))
        data.update({'bednet_util__count': bednet_util['encounter__count']})
        dwr = DrinkingWaterReport.objects.filter(encounter__chw=self)\
                                                .aggregate(Count('encounter'))
        data.update({'drinking_water__count': dwr['encounter__count']})
        sanitation = SanitationReport.objects.filter(encounter__chw=self)\
                                                .aggregate(Count('encounter'))
        data.update({'sanitation__count': sanitation['encounter__count']})
        for item in data:
            if data[item] is None:
                data[item] = '-'
        return data

    @classmethod
    def healthy_survey_columns(cls):
        columns = []
        columns.append({'name': _(u"CHW"), 'bit': '{{object}} '\
                                            '{{object.mobile_phone}}'})
        columns.append({'name': _(u"# of Households"), \
                'bit': '{{object.number_of_households}}'})
        columns.append({'name': _(u"# of HH Visits (Last two weeks)"), \
                'bit': '{{object.two_weeks_visits}}'})
        columns.append({'name': _(u"# of Households Surveyed"), \
                'bit': '{{object.bednet_aggregates.encounter__count}}'})
        columns.append({'name': _(u"# of Sleeping Sites"), \
                'bit': '{{object.bednet_aggregates.sleeping_sites__sum}}'})
        columns.append({'name': _(u"# of Functioning Bednets"), \
                'bit': '{{object.bednet_aggregates.function_nets__sum}}'})
        columns.append({'name': _(u"# of damaged"), \
                'bit': '{{object.bednet_aggregates.damaged_nets__sum}}'})
        columns.append({'name': _(u"# of Earlier Bednets"), \
                'bit': '{{object.bednet_aggregates.earlier_nets__sum}}'})
        columns.append({'name': _(u"# of Bednet Utilization Reports"), \
                'bit': '{{object.bednet_aggregates.bednet_util__count}}'})
        columns.append({'name': _(u"# of Drinking Water Reports"), \
                'bit': '{{object.bednet_aggregates.drinking_water__count}}'})
        columns.append({'name': _(u"# of Sanitation Reports"), \
                'bit': '{{object.bednet_aggregates.sanitation__count}}'})

        return columns

    def households_not_surveyed(self):
        surveyed = BedNetReport.objects.filter(encounter__chw=self)\
                                        .values('encounter__patient')
        not_surveyed = self.households().exclude(id__in=surveyed)
        return not_surveyed

'''
    The monthly report for CHWs requested
    by Dr. Emma.  The code is not great
    but I don't have any good ideas for
    how to shrink the size.
'''
class MonthlyCHWReport(TheCHWReport):
    class Meta:
        proxy = True

    # The report rows.  Returns a list of tuples
    # that can be used to instantiate Indicator objects
    def report_rows(self):
        return [
            ('Households',\
                self.num_of_hhs, Indicator.AVG),
            ('HH Visits',\
                self.num_of_hh_visits, Indicator.SUM),
            Indicator.EMPTY,
            ('Num of Women 15-49 Seen',\
                self.num_of_women_under50_seen, Indicator.SUM),
            ('Num of Women using FP',\
                self.num_of_women_under50_using_fp, Indicator.SUM),
            ('% of Women using FP',\
                self.perc_of_women_under50_using_fp, \
                    Indicator.AGG_PERCS, \
                    Indicator.PERC_PRINT),
            ('Num of Women using FP: Condom',\
                self.num_fp_usage_condom, Indicator.SUM),
            ('Num of Women using FP: Injectable',\
                self.num_fp_usage_injectable, Indicator.SUM),
            ('Num of Women using FP: IUD',\
                self.num_fp_usage_iud, Indicator.SUM),
            ('Num of Women using FP: Implant',\
                self.num_fp_usage_implant, Indicator.SUM),
            ('Num of Women using FP: Pill',\
                self.num_fp_usage_pill, Indicator.SUM),
            ('Num of Women using FP: Ster.',\
                self.num_fp_usage_sterilization, Indicator.SUM),
            ('Num of Women Starting FP or Never Registered',\
                self.num_starting_fp, Indicator.SUM),
            ('Num of Women Remaining on FP',\
                self.num_still_on_fp, Indicator.SUM),
            ('Num of Women Stopping FP',\
                self.num_ending_fp, Indicator.SUM),
            Indicator.EMPTY,
            ('People with DSs',\
                self.num_danger_signs, Indicator.SUM),
            ('People with Referred',\
                self.num_referred, Indicator.SUM),
            ('Num Follow Up Within 3 Days',\
                self.num_ontime_follow_up, Indicator.SUM),
            ('% Follow Up Within 3 Days',\
                self.perc_ontime_follow_up, 
                Indicator.AGG_PERCS, Indicator.PERC_PRINT),
            Indicator.EMPTY,
            ('Num Pregnant Women',\
                self.num_pregnant_by_week, Indicator.AVG),
            ('% Getting 1 ANC by 1st Trim.',\
                self.perc_with_anc_first, 
                Indicator.AGG_PERCS, Indicator.PERC_PRINT),
            ('% Getting 3 ANC by 2nd Trim.',\
                self.perc_with_anc_second, 
                Indicator.AGG_PERCS, Indicator.PERC_PRINT),
            ('% Getting 4 ANC by 3rd Trim.',\
                self.perc_with_anc_third, 
                Indicator.AGG_PERCS, Indicator.PERC_PRINT),
            ('Num Births',\
                self.num_births, Indicator.SUM),
            ('Num Births with 4 ANC',\
                self.num_births_with_anc, Indicator.SUM),
            ('Num Neonatal Rpts (<28 days)',\
                self.num_neonatal, Indicator.SUM),
            Indicator.EMPTY,
            ('Num Children U5',\
                self.num_underfive, Indicator.AVG),
            ('Num U5 Known Immunized',\
                self.num_underfive_imm, Indicator.AVG),
            ('Num MUACs Taken',\
                self.num_muacs_taken, Indicator.SUM),
            ('Num active SAM Cases',\
                self.num_active_sam_cases, Indicator.AVG),
            ('Num Tested RDTs',\
                self.num_tested_rdts, Indicator.SUM),
            ('Num Positive RDTs',\
                self.num_positive_rdts, Indicator.SUM),
            ('Num Anti-Malarials Given',\
                self.num_antimalarials_given, Indicator.SUM),
            ('Num Diarrhea Cases',\
                self.num_diarrhea, Indicator.SUM),
            ('Num ORS Given',\
                self.num_ors_given, Indicator.SUM),
        ]

    #
    # HH Visit section
    #

    def num_of_hhs(self, week_num):
        return self.households(reporting_week_sunday(week_num)).count()

    def num_of_hh_visits(self, weekNum):
        return HouseholdVisitReport\
            .indicators\
            .for_chw(self)\
            .for_reporting_week(weekNum)\
            .count()

    #
    # Family planning section
    #

    def num_of_women_under50_seen(self, week_num):
        return self._num_of_women_count('women', week_num)
    
    def num_of_women_under50_using_fp(self, week_num):
        return self._num_of_women_count('women_using', week_num)

    def perc_of_women_under50_using_fp(self, week_num):
        u50 = self.num_of_women_under50_seen(week_num)
        return (self.num_of_women_under50_using_fp(week_num), u50)

    def _num_of_women_count(self, count_str, week_num):
        if count_str not in ['women','women_using']:
            raise ValueError('Invalid aggregation string.')

        count = FamilyPlanningReport\
            .indicators\
            .for_chw(self)\
            .for_reporting_week(week_num)\
            .aggregate(Sum(count_str))[count_str+'__sum']
        return 0 if count is None else count
    
    def num_fp_usage_condom(self, week_num):
        return self._fp_usage_count('c', week_num)

    def num_fp_usage_injectable(self, week_num):
        return self._fp_usage_count('i', week_num)

    def num_fp_usage_iud(self, week_num):
        return self._fp_usage_count('iud', week_num)

    def num_fp_usage_implant(self, week_num):
        return self._fp_usage_count('n', week_num)

    def num_fp_usage_pill(self, week_num):
        return self._fp_usage_count('p', week_num)

    def num_fp_usage_sterilization(self, week_num):
        return self._fp_usage_count('st', week_num)

    def _fp_usage_count(self, code, week_num):
        fp = CodedItem\
            .objects\
            .filter(type=CodedItem.TYPE_FAMILY_PLANNING)\
            .get(code=code)

        count = FamilyPlanningReport\
            .indicators\
            .for_chw(self)\
            .for_reporting_week(week_num)\
            .filter(familyplanningusage__method__code=fp.code)\
            .aggregate(Sum('familyplanningusage__count'))\
            ['familyplanningusage__count__sum']
        return 0 if count is None else count

    def num_starting_fp(self, week_num):
        return self._fp_change_stats(week_num)[0]

    def num_still_on_fp(self, week_num):
        return self._fp_change_stats(week_num)[1]

    def num_ending_fp(self, week_num):
        return self._fp_change_stats(week_num)[2]

    def _fp_change_stats(self, week_num):
        reps = FamilyPlanningReport\
            .indicators\
            .for_chw(self)\
            .for_reporting_week(week_num)\
            .order_by('-encounter__encounter_date')

        start_count = 0
        same_count = 0
        end_count = 0

        seen = []

        # Get all FP reports in this week
        for r in reps:
            # Count each household only once
            if r.encounter.patient.pk in seen:
                continue
            else:
                seen.append(r.encounter.patient.pk)

            try:
                # Check if there's a previous FP report for this HH
                old_rep = FamilyPlanningReport\
                    .indicators\
                    .filter(encounter__patient__pk=r.encounter.patient.pk,\
                        encounter__encounter_date__lt=r.encounter.encounter_date)\
                    .exclude(pk=r.pk)\
                    .latest('encounter__encounter_date')
            except FamilyPlanningReport.DoesNotExist:
                # If not, count all women as new to FP
                start_count += r.women_using
            else:
                if r.women_using is None:
                    if old_rep.women_using is None: continue
                    end_count += old_rep.women_using
                elif old_rep.women_using is None:
                    if r.women_using is None: continue
                    start_count += r.women_using
                else:
                    # Otherwise calculate change from last FP report
                    if r.women_using > old_rep.women_using:
                        start_count += (r.women_using - old_rep.women_using)
                    elif r.women_using < old_rep.women_using:
                        end_count += (old_rep.women_using - r.women_using)
                    else:
                        same_count += r.women_using

        return (start_count, same_count, end_count)

    #
    # Danger signs section
    #

    def num_danger_signs(self, week_num):
        count = DangerSignsReport\
            .indicators\
            .for_chw(self)\
            .for_reporting_week(week_num)\
            .count()
        return 0 if count is None else count

    def num_referred(self, week_num):
        return ReferralReport\
                .indicators\
                .for_chw(self)\
                .for_reporting_week(week_num)\
                .count()

    def num_ontime_follow_up(self, week_num):
        count = 0
        for r in ReferralReport\
            .indicators\
            .for_chw(self)\
            .for_reporting_week(week_num):

            due_by = r.encounter.encounter_date + timedelta(2)
            f = FollowUpReport\
                .indicators\
                .for_chw(self)\
                .filter(encounter__patient__pk=r.encounter.patient.pk,\
                    encounter__encounter_date__lte=due_by,
                    encounter__encounter_date__gt=\
                        r.encounter.encounter_date)\
                .count()

            if f is None or f == 0:
                continue
            else:
                count += 1
        return count 

    def perc_ontime_follow_up(self, week_num):
        return (self.num_ontime_follow_up(week_num),\
            self.num_referred(week_num))

    #
    # Pregnancy section
    #
    
    def pregnant_by_week(self, week_num):
        return self.pregnant_women(reporting_week_sunday(week_num))
    
    def num_pregnant_by_week(self, week_num):
        return len(self.pregnant_by_week(week_num))

    # % of women getting at least 1 ANC visit by 1st trimester
    def perc_with_anc_first(self, week_num):
        return self._women_getting_n_anc_by(1, 1, week_num)

    # % of women getting at least 3 ANC visits by 2nd trimester
    def perc_with_anc_second(self, week_num):
        return self._women_getting_n_anc_by(3, 2, week_num)

    # % of women getting at least 4 ANC visits by 3rd trimester
    def perc_with_anc_third(self, week_num):
        return self._women_getting_n_anc_by(4, 3, week_num)

    def _women_getting_n_anc_by_tot(self, n_anc, trimester):
        if trimester not in xrange(1,4):
            raise ValueError('Trimester is out of range [1,3]')

        women = []
        for wk in xrange(0,4):
            for w in self._women_in_month_of_preg(trimester, wk):
                if w not in women:
                    women.append(w)
        have_anc = filter(lambda w: w.anc_visits > n_anc, women)

        return (len(have_anc), len(women))

    def _women_getting_n_anc_by(self, n_anc, trimester, week_num):
        if trimester not in xrange(1,4):
            raise ValueError('Trimester is out of range [1,3]')

        women = self._women_in_month_of_preg(trimester, week_num)
        have_anc = filter(lambda w: w.anc_visits >= n_anc, women)
       
        return (len(have_anc), len(women))
        
    
    def _women_in_month_of_preg(self, trimester, week_num):
        if trimester not in xrange(1,4):
            raise ValueError('Trimester is out of range [1,3]')

        # e.g., 2nd trimester is range(4, 7)
        end_mo = (trimester*3)+1
        start_mo = end_mo - 3
        month_range = xrange(start_mo, end_mo)

        women = self.pregnant_by_week(week_num)

        # Get latest pregnancy report for woman
        preggers = map(lambda w:
            PregnancyReport\
                .objects\
                .filter(encounter__patient=w, \
                    encounter__encounter_date__gte=\
                        reporting_week_monday(week_num) - \
                            timedelta(30.4375 * 10))
                .latest('encounter__encounter_date'), women)

        # See how many women fall in this trimester
        targets = []
        for p in preggers:
            days_ago = (reporting_week_sunday(week_num) - \
                p.encounter.encounter_date).days
            months_ago = days_ago / 30.4375
            months_of_preg = p.pregnancy_month + months_ago

            if round(months_of_preg) in month_range:
                targets.append(p)

        return targets

    def _births(self, week_num):
        return BirthReport\
            .indicators\
            .for_chw(self)\
            .for_reporting_week(week_num)\

    def num_births(self, week_num):
        return self._births(week_num).count()

    def num_births_with_anc(self, week_num):
        births = self._births(week_num)
        count = 0
        for b in births:
            if b.encounter.patient.mother is None:
                continue
            mother = b.encounter.patient.mother

            try: 
                prep = PregnancyReport\
                    .objects\
                    .filter(encounter__patient=mother)\
                    .filter(encounter__encounter_date__gte=\
                        datetime.today() - timedelta(30.4375 * 10))\
                    .latest('encounter__encounter_date')
            except PregnancyReport.DoesNotExist:
                continue

            # 4 is number of ANC visits to have at term
            if prep.anc_visits >= 4:
                count += 1

        return count

    def num_neonatal(self, week_num):
        return NeonatalReport\
            .indicators\
            .for_chw(self)\
            .for_reporting_week(week_num)\
            .count()

    def num_underfive(self, week_num):
        return self.patients_under_five(\
            reporting_week_sunday(week_num)).count()

    def num_underfive_imm(self, week_num):
        return self._num_underfive_imm_pks(week_num).count()

    def _num_underfive_imm_pks(self, week_num):
        return UnderOneReport\
            .indicators\
            .for_chw(self)\
            .before_reporting_week(week_num)\
            .filter(immunized=UnderOneReport.IMMUNIZED_YES)\
            .values('encounter__patient__pk')\
            .distinct()

    def num_muacs_taken(self, week_num):
        return NutritionReport\
            .indicators\
            .for_chw(self)\
            .for_reporting_week(week_num)\
            .count()

    def num_active_sam_cases(self, week_num):
        return self.num_of_active_sam_cases(\
            reporting_week_sunday(week_num))

    def num_tested_rdts(self, week_num):
        return FeverReport\
            .indicators\
            .for_chw(self)\
            .for_reporting_week(week_num)\
            .exclude(rdt_result=FeverReport.RDT_UNKOWN)\
            .count()

    def num_positive_rdts(self, week_num):
        return FeverReport\
            .indicators\
            .for_chw(self)\
            .for_reporting_week(week_num)\
            .filter(rdt_result=FeverReport.RDT_POSITIVE)\
            .count()

    def num_antimalarials_given(self, week_num):
        return MedicineGivenReport\
            .indicators\
            .for_chw(self)\
            .for_reporting_week(week_num)\
            .filter(medicines__code='act')\
            .count()

    def num_diarrhea(self, week_num):
        return DangerSignsReport\
            .indicators\
            .for_chw(self)\
            .for_reporting_week(week_num)\
            .filter(danger_signs__code='dr')\
            .count()

    def num_ors_given(self, week_num):
        return MedicineGivenReport\
            .indicators\
            .for_chw(self)\
            .for_reporting_week(week_num)\
            .filter(medicines__code='r')\
            .count()

    #
    # Lists
    #

    # Kids 1-2 yrs needing immunizations
    def needing_immunizations(self):
        imm_pks = map(lambda i: i['encounter__patient__pk'],\
            self._num_underfive_imm_pks(3))

        return Patient\
            .objects\
            .exclude(pk__in=imm_pks)\
            .filter(dob__gte=date.today()-timedelta(2*365.25),\
                dob__lte=date.today()-timedelta(365.25),\
                chw=self)\
            .order_by('location__code')
      
    # Pregnant women in 2nd or 3rd trimester who haven't had 
    # ANC visits in last 5 five weeks
    def pregnant_needing_anc(self):
        pregs = PregnancyReport\
            .indicators\
            .for_chw(self)\
            .filter(encounter__encounter_date__gt = \
                date.today() - timedelta(10 * 30.4375))\
            .order_by('-encounter__encounter_date')
        
        no_anc = []
        women = []
        for p in pregs:
            if p.encounter.patient in women:
                continue

            days_ago = (datetime.today() - p.encounter.encounter_date).days
            weeks_ago = days_ago / 7.0
            months_ago = days_ago / 30.4375
           
            # Current month of pregnancy
            preg_month = p.pregnancy_month + months_ago
            if preg_month > 9.0 or preg_month < 3.0:
                continue
         
            print "%s %d %d" % (p.encounter.encounter_date, p.pregnancy_month, preg_month)
            months_left = 9 - preg_month 
            days_left = months_left * 30.475
            due_date = date.today() + timedelta(days_left)
            
            # Current weeks since ANC
            if p.weeks_since_anc is None:
                no_anc.append((p.encounter.patient, \
                    None,\
                    due_date))
            else:
                weeks_since_anc = p.weeks_since_anc + weeks_ago
                if weeks_since_anc > 5.0:
                    women.append((p.encounter.patient, \
                        p.encounter.encounter_date, \
                        due_date))

        women.sort(lambda x,y: cmp(x[1],y[1]))
        return (no_anc + women)
            
    def kids_needing_muac(self):
        # people eligible for MUAC
        muac_list = self.muac_list()\
            .order_by('encounter__patient__location__code')
       
        seen = []
        need_muac = []
        no_muac = []

        one_month_ago = datetime.today() - timedelta(30.4375)
        three_months_ago = datetime.today() - timedelta(3 * 30.4375)

        danger = (NutritionReport.STATUS_SEVERE, \
                        NutritionReport.STATUS_SEVERE_COMP)
        for p in muac_list:
            if p.pk in seen:
                continue
            else:
                seen.append(p.pk)

            try:
                nut = NutritionReport\
                    .objects\
                    .filter(encounter__patient__pk=p.pk)\
                    .latest('encounter__encounter_date')
            except NutritionReport.DoesNotExist:
                no_muac.append((p, None))
                continue

            if nut.status in danger and \
                    nut.encounter.encounter_date < one_month_ago:
                need_muac.append((p, nut))
            elif nut.encounter.encounter_date < three_months_ago:
                need_muac.append((p, nut))
            else:
                pass
        
        need_muac.sort(lambda x,y:\
            cmp(x[1].encounter.encounter_date, \
                y[1].encounter.encounter_date))
        return no_muac + need_muac


