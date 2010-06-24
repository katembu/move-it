#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.utils.translation import gettext as _
from django.db.models import F

from datetime import date, timedelta, datetime

from childcount.models import Patient
from childcount.models import CHW
from childcount.models import NutritionReport, FeverReport, ReferralReport
from childcount.models import BirthReport, PregnancyReport
from childcount.models import HouseholdVisitReport, FollowUpReport

from childcount.utils import day_end, day_start, get_dates_of_the_week, \
                                get_median

from logger.models import IncomingMessage, OutgoingMessage


class ThePatient(Patient):

    class Meta:
        verbose_name = _("Patient List Report")
        proxy = True

    def latest_muac(self):
        muac = NutritionReport.objects.filter(patient=self).latest()
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
            nr = NutritionReport.objects.filter(encounter__patient=self).latest()
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
            'bit': '{{object.last_name}} {{object.first_name}}'})
        columns.append(
            {'name': cls._meta.get_field('gender').verbose_name.upper(), \
            'bit': '{{object.gender}}'})
        columns.append(
            {'name': _("Age".upper()), \
            'bit': '{{object.humanised_age}}'})
        columns.append(
            {'name': _("Last muac".upper()), \
            'bit': '{{object.latest_muac}}'})
        columns.append(
            {'name': cls._meta.get_field('chw').verbose_name.upper(), \
            'bit': '{{object.chw}}'})

        sub_columns = None
        return columns, sub_columns

    def patient_register_columns(cls):
        columns = []
        columns.append(
            {'name': cls._meta.get_field('health_id').verbose_name.upper(), \
            'bit': '{{object.health_id.upper}}'})
        columns.append(
            {'name': _("Name".upper()), \
            'bit': '{{object.last_name}} {{object.first_name}}'})
        columns.append(
            {'name': cls._meta.get_field('gender').verbose_name.upper(), \
            'bit': '{{object.gender}}'})
        columns.append(
            {'name': _("Age".upper()), \
            'bit': '{{object.humanised_age}}'})
        columns.append(
            {'name': _("status".upper()), \
            'bit': '{{object.status}}'})    
        return columns


class TheCHWReport(CHW):

    class Meta:
        verbose_name = _("Community Health Worker Report")
        proxy = True

    @property
    def num_of_patients(self):
        num = Patient.objects.filter(chw=self).count()
        return num

    @property
    def num_of_underfive(self):
        return self.patients_under_five().count()

    def patients_under_five(self):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        return Patient.objects.filter(chw=self, dob__lte=sixtym)

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
                                status=NutritionReport.STATUS_MODERATE).count()
        return num

    @property
    def num_of_healthy(self):
        num = NutritionReport.objects.filter(created_by=self, \
                                status=NutritionReport.STATUS_HEALTHY).count()
        return num

    @property
    def num_of_visits(self):
        '''The number of visits in the last 7 days'''
        seven = date.today() - timedelta(7)
        num = HouseholdVisitReport.objects.filter(created_by=self).count()
        return num

    @property
    def num_muac_eligible(self):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        sixm = date.today() - timedelta(int(30.4375 * 6))
        num = Patient.objects.filter(chw=self, dob__gte=sixtym, \
                                     dob__lte=sixm).count()
        return num

    @classmethod
    def total_muac_eligible(cls):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        sixm = date.today() - timedelta(int(30.4375 * 6))
        num = Patient.objects.filter(dob__gte=sixtym, \
                                     dob__lte=sixm).count()
        return num

    @property
    def num_of_sms(self):
        identity = self.connection().identity
        num = IncomingMessage.objects.filter(identity=identity).count()
        return num

    @property
    def number_of_households(self):
        return self.households().count()

    def households(self):
        return Patient.objects.filter(health_id=F('household__health_id'), \
                                        chw=self)

    def num_of_householdvisits(self):
        return HouseholdVisitReport.objects.filter(encounter__chw=self).count()

    def percentage_ontime_visits(self):
        households = self.households()
        num_on_time = 0
        for household in households:
            thepatient = ThePatient.objects.get(health_id=household.health_id)
            if thepatient.visit_within_90_days_of_last_visit():
                num_on_time += 1
        if num_on_time is 0:
            return 0
        else:
            total_households = households.count()
            return int(round((num_on_time/float(total_households))*100))

    def num_of_births(self):
        return BirthReport.objects.filter(encounter__chw=self).count()

    def percentage_ontime_birth_visits(self):
        births = BirthReport.objects.filter(encounter__chw=self)
        count = 0
        for birth in births:
            thepatient = ThePatient.objects.get(id=birth.encounter.patient)
            if thepatient.check_visit_within_seven_days_of_birth():
                count += 1
        if not count:
            return count
        return int(round(100 * (count/float(births.count()))))

    def num_of_clinic_delivery(self):
        return BirthReport.objects.filter(encounter__chw=self, \
                        clinic_delivery=BirthReport.CLINIC_DELIVERY_YES).count()

    def percentage_clinic_deliveries(self):
        num_of_clinic_delivery = self.num_of_clinic_delivery()
        num_of_births = self.num_of_births()
        if num_of_births == 0:
            return 0
        return int(round(num_of_clinic_delivery/float(num_of_births))*100)

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
    
    def num_underfive_diarrhea(self):
        #TODO
        return 0

    def percentage_ontime_muac(self):
        underfives = self.patients_under_five()
        count = 0
        for achild in underfives:
            thepatient = ThePatient.objects.get(id=achild.id)
            if thepatient.ontime_muac():
                count += 1
        if not count:
            return count
        else:
            total_count = underfives.count()
            return int(round(100 * (count/float(total_count))))

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
            return int(round(100*(count/float(total_count))))

    def percentage_ontime_followup(self):
        referrals = ReferralReport.objects.filter(encounter__chw=self)
        if not referrals:
            return ''
        num_referrals = referrals.count()
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
        return '%s%%' % int(round((ontimefollowup / \
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
        total_sms = IncomingMessage.objects.filter(identity=self.connection()\
                                    .identity).count()
        if total_sms == 0:
            return 0
        total_error_sms = OutgoingMessage.objects.filter(identity=self\
                                    .connection().identity, \
                                    text__icontains='error').count()
        return int(round((total_error_sms / float(total_sms)) * 100))

    def days_since_last_sms(self):
        now = datetime.now()
        last_sms = IncomingMessage.objects.filter(identity=self.connection()\
                                    .identity, received__lte=now)\
                                    .order_by('-received')
        if not last_sms:
            return None
        return (now - last_sms[0].received).days

    @classmethod
    def muac_summary(cls):
        num_healthy = NutritionReport.objects.filter(\
                        status=NutritionReport.STATUS_HEALTHY).count()
        num_mam = NutritionReport.objects.filter(\
                        status=NutritionReport.STATUS_MODERATE).count()
        num_sam = NutritionReport.objects.filter(\
                        status=NutritionReport.STATUS_SEVERE).count()
        num_comp = NutritionReport.objects.filter(\
                        status=NutritionReport.STATUS_SEVERE_COMP).count()
        num_eligible = TheCHWReport.total_muac_eligible()
        info = {'%s%% HEALTHY' %\
                int(round((num_healthy / float(num_eligible)) * 100)): num_healthy,
                '%s%% MAM' %\
                    int(round((num_mam / float(num_eligible)) * 100)): num_mam,
                '%s%% SAM' %\
                    int(round((num_sam / float(num_eligible)) * 100)): num_sam,
                '%s%% SAM+' %\
                    int(round((num_comp / float(num_eligible)) * 100)): num_comp}
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
    def sms_per_day(cls):
        days_of_the_week = get_dates_of_the_week()
        data = {}
        for day in days_of_the_week:
            start = day_start(day['date'])
            end = day_end(day['date'])
            num = IncomingMessage.objects.filter(received__gte=start, \
                                           received__lte=end).count()
            data.update({day["day"]: num})
        return data

class OperationalReport():
    columns = []
    def __init__(self):
        columns = []
        columns.append({'name': _("CHW"), 'bit': '{{object}}'})
        columns.append({'name': _("# of Households"), \
                'bit': '{{object.number_of_households}}'})
        columns.append({'name': _("# of Household Visits"), \
                'bit': '{{object.num_of_householdvisits}}'})
        columns.append({'name': _("% of HHs receiving on-time routine visit "\
                                    "(within 90 days) [S23]"), \
                'bit': '{{object.percentage_ontime_visits}}%'})
        columns.append({'name': _("# of Births"), \
                'bit': '{{object.num_of_births}}'})
        columns.append({'name': _("% Births delivered in Health Facility [S4]"),
                'bit': '{{object.percentage_clinic_deliveries}}%'})
        columns.append({'name': _("% Newborns checked within 7 days of birth "\
                            "[S6]"), \
                'bit': '{{object.percentage_ontime_birth_visits}}%'})
        columns.append({'name': _("# of Under-5s"), \
                'bit': '{{object.num_of_underfive}}'})
        columns.append({'name': _("# Under-5 Referred for Danger Signs"), \
                'bit': '{{object.num_underfive_refferred}}'})
        columns.append({'name': _("# Under-5 Treated for Malarias"), \
                'bit': '{{object.num_underfive_malaria}}'})
        columns.append({'name': _("# Under-5 Treated for Diarrhea"), \
                'bit': '{{object.num_underfive_diarrhea}}'})
        columns.append({'name': _("% Under-5 receiving on-time MUAC "\
                                    "(within 90 days) [S11]"), \
                'bit': '{{object.percentage_ontime_muac}}%'})
        columns.append({'name': _("# of Active GAM cases"), \
                'bit': '{{object.num_of_active_sam_cases}}'})
        columns.append({'name': _("# of Pregnant Women"), \
                'bit': '{{object.num_of_pregnant_women}}'})
        columns.append({'name': _("# Pregnant Women Referred for Danger Signs"),
                'bit': '{{object.num_pregnant_refferred}}'})
        columns.append({'name': _("% Pregnant receiving on-time visit"\
                        " (within 6 weeks) [S24]"), \
                'bit': '{{object.percentage_pregnant_ontime_visits}}'})
        columns.append({'name': _("% Referred / Treated receiving on-time "\
                                    "follow-up (within 2 days) [S13]"),
                'bit': '{{object.percentage_ontime_followup}}'})
        columns.append({'name': _("Median # of days for follow-up [S25]"), \
                'bit': '{{object.median_number_of_followup_days}}'})
        columns.append({'name': _("SMS Error Rate %"),
                'bit': '{{object.sms_error_rate}}%'})
        columns.append({'name': _("Days since last SMS transmission"), \
                'bit': '{{object.days_since_last_sms}}'})
        self.columns = columns

    def get_columns(self):
        return self.columns

