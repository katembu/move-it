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
from childcount.models import FeverReport
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

from childcount.utils import day_end, \
                                day_start, \
                                get_dates_of_the_week, \
                                get_median, \
                                seven_days_to_date, \
                                first_day_of_month, \
                                last_day_of_month

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

    def patients_under_five(self):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
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
    def number_of_households(self):
        return self.households().count()

    def households(self):
        '''
        List of households belonging to this CHW
        '''
        return Patient.objects.filter(health_id=F('household__health_id'), \
                                        chw=self, status=Patient.STATUS_ACTIVE)

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

    def num_of_active_sam_cases(self):
        count = 0
        danger = (NutritionReport.STATUS_SEVERE, \
                        NutritionReport.STATUS_SEVERE_COMP)
        nr = NutritionReport.objects\
                        .filter(encounter__chw=self, status__in=danger)\
                        .values('encounter__patient').distinct()
        for r in nr:
            p = Patient.objects.get(id=r['encounter__patient'])
            latest = NutritionReport.objects.filter(encounter__patient=p)\
                                            .latest()
            if latest.status in danger:
                count += 1
        return count

    def num_of_pregnant_women(self):
        return len(self.pregnant_women())

    def pregnant_women(self):
        c = []
        pregs = PregnancyReport.objects.filter(encounter__chw=self)\
                                .values('encounter__patient').distinct()
        for preg in pregs:
            patient = Patient.objects.get(id=preg['encounter__patient'])
            pr = PregnancyReport.objects.filter(encounter__patient=patient)\
                                        .latest()
            days = (pr.encounter.encounter_date - datetime.now()).days
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
    def summary(cls):
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
