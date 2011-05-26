#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga, rgaudin

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
from childcount.models import StillbirthMiscarriageReport
from childcount.models import MedicineGivenReport
from childcount.models import DangerSignsReport
from childcount.models import NeonatalReport
from childcount.models import FamilyPlanningReport
from childcount.models import FeverReport
from childcount.models import CodedItem
from childcount.models import ReferralReport
from childcount.models import BirthReport
from childcount.models import PregnancyReport, SPregnancy
from childcount.models import HouseholdVisitReport
from childcount.models import FollowUpReport
from childcount.models import ImmunizationSchedule
from childcount.models import ImmunizationNotification
from childcount.models import BedNetReport
from childcount.models import BednetIssuedReport
from childcount.models import BednetUtilization
from childcount.models import DrinkingWaterReport
from childcount.models import SanitationReport
from childcount.models import AppointmentReport
from childcount.models import UnderOneReport
from childcount.models import DeathReport

from childcount.utils import day_end, \
                                day_start, \
                                get_dates_of_the_week, \
                                get_median, \
                                seven_days_to_date, \
                                first_day_of_month, \
                                last_day_of_month, \
                                first_date_of_week

from logger.models import IncomingMessage, OutgoingMessage

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
        return Patient.objects.filter(chw=self, \
                            dob__gte=sixtym, \
                            dob__lte=today,
                            status=Patient.STATUS_ACTIVE)

    @property
    def num_of_under_nine(self):
        return self.patients_under_nine().count()

    def patients_under_nine(self):
        ninem = date.today() - timedelta(int(30.4375 * 9))
        return Patient.objects.filter(chw=self, dob__gte=ninem, \
                            status=Patient.STATUS_ACTIVE)

    def patients_underone(self):
        oney = date.today() - timedelta(int(30.4375 * 12))
        return Patient.objects.filter(chw=self, dob__gte=oney, \
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
        num = IncomingMessage.objects.filter(identity=identity).count()
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
        patients = Patient.objects.filter(chw=self, \
                                     dob__gte=sixtym, \
                                     dob__lte=sixm, \
                                     status=Patient.STATUS_ACTIVE)
        return patients

    def num_of_householdvisits(self):
        return HouseholdVisitReport.objects.filter(encounter__chw=self).count()

    def num_of_householdvisits_90_days(self):
        today = datetime.today().date()
        return self.household_visit(today - timedelta(90), today)

    def num_of_uniq_householdvisits_90_days(self):
        today = datetime.today().date()
        return self._household_visit(today - timedelta(90), today)\
            .values('household__health_id')\
            .distinct()\
            .count()
    
    def household_visit(self, startDate=None, endDate=None):
        return self._household_visit(startDate, endDate).count()
    
    def _household_visit(self, startDate=None, endDate=None):
        return HouseholdVisitReport.objects.filter(encounter__chw=self, \
                                encounter__encounter_date__gte=startDate, \
                                encounter__encounter_date__lte=endDate)

    def household_visits_for_month(self, offset=0):
        # This list comprehension deserves some explanation.
        # First, we get a list of days from 30+offset days ago up
        # to today.
        # Then, we get (day, count) tuples for each of those
        # days, where count contains the number of
        # HH visits for that day by this CHW
        return [(i, self.household_visit(date.today() + timedelta(i), \
            date.today() + timedelta(i + 1))) \
                for i in xrange(-30 - offset, -offset)]

    def percentage_ontime_visits(self):
        (num_on_time, total_households) = \
            self._percentage_ontime_visits_raw()
        if total_households == 0:
            return None
        if num_on_time is 0:
            return 0
        else:
            return int(100.0 * num_on_time / float(total_households))

    def _percentage_ontime_visits_raw(self, relative_to=date.today()):
        households = self.households()
        num_on_time = 0
        for household in households:
            thepatient = ThePatient.objects.get(health_id=household.health_id)
            if thepatient.visit_within_90_days_of_last_visit(relative_to):
                num_on_time += 1
        return (num_on_time, households.count())

    def num_of_births(self):
        return BirthReport.objects.filter(encounter__chw=self).count()

    def percentage_ontime_birth_visits(self):
        births = BirthReport.objects.filter(encounter__chw=self)
        v_count = 0
        b_count = births.count()
        for birth in births:
            thepatient = ThePatient.objects.get(pk=birth.encounter.patient.pk)
            if thepatient.check_visit_within_seven_days_of_birth():
                v_count += 1
        print (v_count, b_count)
        if b_count == 0:
            return None
        elif v_count == 0:
            return 0
        else:
            return int(100.0 * v_count / float(b_count))

    def num_of_clinic_delivery(self):
        return BirthReport.objects.filter(encounter__chw=self, \
                    clinic_delivery=BirthReport.CLINIC_DELIVERY_YES).count()

    def percentage_clinic_deliveries(self):
        num_of_clinic_delivery = self.num_of_clinic_delivery()
        num_of_births = self.num_of_births()
        if num_of_births == 0:
            return None
        else:
            return int(100.0 * num_of_clinic_delivery / float(num_of_births))

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
        (num, den) = self.fraction_ontime_muac()

        if den == 0:
            return None

        if num == 0:
            return 0
        else:
            return int(round(100 * (num/ float(den))))

    def fraction_ontime_muac(self, relativeTo=date.today()):
        # Consider only kids over 6 months
        underfives = self.patients_under_five(relativeTo)
        underfives.filter(dob__lte=(relativeTo-timedelta(180)))

        count = 0
        for achild in underfives:
            thepatient = ThePatient.objects.get(id=achild.id)
            if thepatient.ontime_muac(relativeTo):
                count += 1

        return (count, underfives.count())

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

    def pregnant_women(self, today=datetime.today().date()):
        c = []
        # Need to use Sauri specific
        # Noticed that PregnancyReport.objects.filter(encounter__chw=self)
        # does returns [], with values('encounter__patient').distinct()
        # returns some values but they are different if SPregnancy is used
        if not PregnancyReport.objects.filter(encounter__chw=self):
            prgclass = SPregnancy
        else:
            prgclass = PregnancyReport
        pregs = prgclass\
            .objects\
            .filter(encounter__chw=self, \
                encounter__encounter_date__gt=today-timedelta(365.25),\
                encounter__encounter_date__lte=today)\
            .values('encounter__patient')\
            .distinct()
        print "got %d pregs" % pregs.count()

        for preg in pregs:
            patient = Patient.objects.get(pk=preg['encounter__patient'])
            pr = prgclass\
                .objects\
                .filter(encounter__patient=patient,\
                    encounter__encounter_date__lte=today,\
                    encounter__encounter_date__gt=today-timedelta(365.25))\
                .latest('encounter__encounter_date')

            # Number of days since encounter
            days = (today - pr.encounter.encounter_date.date()).days
            # Number of months since encounter
            months = round(days / 30.4375)

            print 'PR submitted %s at month %d (ago: %d)' % \
                (pr.encounter.encounter_date, pr.pregnancy_month, months)

            # If the pregnancy month plus months since encounter
            # is greater than 9 and there's no birth report,
            # then let's assume the lady is not pregnant
            months_pregnant = pr.pregnancy_month + months
            if months_pregnant > 9:
                print 'too old %d in %s' % \
                    (pr.pregnancy_month, pr.encounter.encounter_date)
                continue

            # Look for a baby since the pregnancy
            b = Patient\
                .objects\
                .filter(mother__pk=pr.encounter.patient.pk,\
                    dob__gte=today-timedelta(months_pregnant*30.4375),\
                    dob__lte=today)

            # If the birthreport has been found, then she's no longer
            # pregnant
            if b.count() > 0:
                print 'birth at %d' % months_pregnant
                continue

            # Look for a stillbirth/miscarriage
            s = StillbirthMiscarriageReport\
                .objects\
                .filter(encounter__patient__pk=pr.encounter.patient.pk,\
                    incident_date__gte=\
                        today-timedelta(months_pregnant*30.4375),\
                    incident_date__lte=today)

            # If there was a stillbirth/misscariage, then she's
            # no longer pregnant
            if s.count() > 0:
                print 'stillbirth'
                continue
            
            print '*PR submitted %s at month %d (ago: %d)' % \
                (pr.encounter.encounter_date, pr.pregnancy_month, months)
            c.append(patient)
        return c

    def num_pregnant_refferred(self):
        pwomen = self.pregnant_women()
        return ReferralReport\
            .objects\
            .filter(\
                encounter__patient__in=pwomen, \
                encounter__chw=self)\
            .exclude(urgency=ReferralReport.URGENCY_CONVENIENT).count()

    def percentage_pregnant_ontime_visits(self):
        pwomen = self.pregnant_women()

        if len(pwomen) == 0:
            return None

        # Check if report submitted was Sauri report or standard
        # report
        if not PregnancyReport.objects.filter(encounter__chw=self):
            prgclass = SPregnancy
        else:
            prgclass = PregnancyReport

        count = 0
        for patient in pwomen:
            pr = prgclass.objects.filter(encounter__patient=patient)\
                                        .latest('encounter__encounter_date')
            latest_date = pr.encounter.encounter_date
            old_date = latest_date - timedelta(6 * 7)
            pr = prgclass.objects.filter(encounter__patient=patient, \
                                encounter__encounter_date__gte=latest_date, \
                                encounter__encounter_date__lt=old_date)
            if pr.count():
                count += 1
        if not count:
            return count
        else:
            total_count = len(pwomen)
            return int(round(100 * (count / float(total_count))))

    def people_without_followup(self, start_date=date(1901,01,01),\
            end_date=date.today()):

        print (start_date, end_date)
        referrals = ReferralReport\
            .objects\
            .filter(encounter__chw=self, \
                encounter__encounter_date__lte=end_date,\
                encounter__encounter_date__gte=start_date)\
            .exclude(urgency=ReferralReport.URGENCY_CONVENIENT)

        num_referrals = referrals.count()
        if num_referrals == 0:
            print "No referrals"
            return None

        ontime = []
        nofup = []
        for referral in referrals:
            rdate = referral.encounter.encounter_date
            day2later = day_end(rdate + timedelta(3))
            try:
                fur = FollowUpReport.objects.filter(encounter__chw=self, \
                            encounter__patient=referral.encounter.patient, \
                            encounter__encounter_date__gt=rdate, \
                            encounter__encounter_date__lte=day2later)
            except FollowUpReport.DoesNotExist:
                pass
                print "Ref: %s, FU: None" % rdate.date()

            if fur.count() > 0:
                print "Ref: %s, FU: %s" % (rdate.date(), \
                    fur[0].encounter.encounter_date.date())
                ontime.append(referral)
            else:
                nofup.append(referral)
                print "Ref: %s, FU: None" % rdate.date()

        return (ontime, nofup)

    def percentage_ontime_followup(self, start_date=date(1901,01,01),\
            end_date=date.today(), raw=False):

        out = self.people_without_followup(start_date, end_date)
        if out is None:
            return None

        (ontime, nofup) = out
        n_ontime = len(ontime)
        n_nofup = len(nofup)
        n_total = n_ontime + n_nofup

        if raw:
            return (n_ontime, n_total)
        else:
            return int(round((n_ontime/ \
                        float(n_total)) * 100))

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
            return None
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
        p['underone'] = self.patients_underone().count()

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
        p['underone'] = self.patients_underone().count()

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

    def current_monthly_appointments(self):
        '''AppointmentReports since the start of the month to date'''
        today = datetime.today().date()
        start_of_month = today - timedelta(today.day - 1)
        apts = AppointmentReport.objects.filter(encounter__chw=self,
                                appointment_date__gte=start_of_month,
                                appointment_date__lte=today)
        return apts

    def num_of_appointment(self):
        return self.current_monthly_appointments().count()

    def percentage_reminded(self):
        apts = self.current_monthly_appointments()
        total = apts.count()
        reminded = apts.filter(status__in=(AppointmentReport.STATUS_PENDING_CV,
                                            AppointmentReport.STATUS_CLOSED))
        if total == 0:
            return None
        return int(round((reminded.count() / float(total)) * 100, 0))

    def score(self):
        pov = pobv = pom = ppov = pr = pof = 0
        div_by = 0
        if self.percentage_ontime_visits():
            pov = self.percentage_ontime_visits()
            div_by += 1
        if self.percentage_ontime_birth_visits():
            pobv = self.percentage_ontime_birth_visits()
            div_by += 1
        if self.percentage_ontime_muac():
            pom = self.percentage_ontime_muac()
            div_by += 1
        if self.percentage_pregnant_ontime_visits():
            ppov = self.percentage_pregnant_ontime_visits()
            div_by += 1
        if self.percentage_reminded():
            pr = self.percentage_reminded()
            div_by += 1
        if self.percentage_ontime_followup():
            pof = self.percentage_ontime_followup()
            div_by += 1
        score =  pov + pobv + pom + ppov + pof + pr

        if div_by == 0:
            return None

        return int(round(score / float(div_by), 0))

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
    def muac_summary_data():
        """
        Copy/Pasted from muac_summary to get the same data but in a dict, rather than
        a string.
        """
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
        return {'healthy':hp, 'moderate': modp, 'unknown': unkp }


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
            num = IncomingMessage.objects.filter(received__gte=start, \
                                           received__lte=end).count()
            total_error_sms = OutgoingMessage.objects.filter(sent__gte=start, \
                                           sent__lte=end, \
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
        num += NutritionReport.objects.filter(\
                            status=NutritionReport.STATUS_MODERATE, \
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
                            status=NutritionReport.STATUS_MODERATE).count()
        num += NutritionReport.objects.filter(\
                                status=NutritionReport.STATUS_SEVERE).count()
        num += NutritionReport.objects.filter(\
                                status=NutritionReport.STATUS_SEVERE_COMP).count()


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

