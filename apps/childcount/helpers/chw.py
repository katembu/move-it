#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from datetime import timedelta

from django.utils.translation import gettext as _

from childcount.indicators import registration
from childcount.indicators import household
from childcount.indicators import family_planning
from childcount.indicators import danger_signs
from childcount.indicators import referral
from childcount.indicators import follow_up
from childcount.indicators import pregnancy
from childcount.indicators import birth
from childcount.indicators import neonatal
from childcount.indicators import under_one
from childcount.indicators import nutrition
from childcount.indicators import fever
from childcount.indicators import medicine_given

from childcount.models import Patient
from childcount.models.reports import PregnancyReport
from childcount.models.reports import FollowUpReport
from childcount.models.reports import ReferralReport
from childcount.models.reports import NutritionReport

report_indicators = (
    {
        'title': _("Household"),
        'columns': [
            {'name': _("Households"), 'ind': registration.Household},
            {'name': _("Total HH Visits"), 'ind': household.Total},
            {'name': _("% HH Coverage"), 'ind': household.CoveragePerc}
        ]
    },
    {
        'title': _("Family Planning"),
        'columns': [
            {'name': _("Women 15-49 Seen"), 'ind': family_planning.Women},
            {'name': _("Women Using FP"), 'ind': family_planning.Using},
            {'name': _("Women Starting FP (or Never Registered)"),
                'ind': family_planning.Starting},
        ]
    },
    {
        'title': _("Follow Up"),
        'columns': [
            {'name': _("People with DSs"), 'ind': danger_signs.Total},
            {'name': _("Urgent (Non-Convenient) Referrals"),
                'ind': referral.Urgent},
            {'name': _("On-Time Follow-Up Visits (between 18 and 72 hours)"), \
                'ind': follow_up.OnTime},
            {'name': _("Late Follow-Up Visits (between 72 hours and 7 days)"), \
                'ind': follow_up.Late},
            {'name': _("No Follow-Up Visits (never or after 7 days)"), \
                'ind': follow_up.Never},
        ]
    },
    {
        'title': _("Pregnancy"),
        'columns': [
            {'name': _("Pregnant Women"), 'ind': pregnancy.Total},
            {'name': _("Births"), 'ind': birth.Total},
            {'name': _("Births with 4 ANC"), 'ind': birth.WithAncFour},
            {'name': _("Babies Known Delivered in Clinic"), \
                'ind': birth.DeliveredInClinic},
            {'name': _("Neonatal Reports (within 7 days)"), \
                'ind': neonatal.WithinSevenDaysOfBirth},
        ]
    },
    {
        'title': _("Under Five"),
        'columns': [
            {'name': _("Children U5"), 'ind': registration.UnderFive},
            {'name': _("Children U5 Known Immunized"),\
                'ind': under_one.UnderFiveImmunizationUpToDate},
            {'name': _("MUACs Taken"), 'ind': nutrition.Total},
            {'name': _("Active SAM/MAM Cases"), 'ind': nutrition.SamOrMam},
        ]
    },
    {
        'title': _("Malaria"),
        'columns': [
            {'name': _("Tested RDTs"), 'ind': fever.Total},
            {'name': _("Positive RDTs"), 'ind': fever.RdtPositive},
            {'name': _("Anti-malarials Given"), 'ind': medicine_given.Antimalarial},
        ]
    },
    {
        'title': _("Diarrhea"),
        'columns': [
            {'name': _("U5 Diarrhea Cases"), 'ind': danger_signs.UnderFiveDiarrhea},
            {'name': _("ORS Given"), 'ind': medicine_given.Ors},
        ]
    },
)


def pregnant_needing_anc(period, chw):
    """Pregnant women in 2nd or 3rd trimester who haven't had
    ANC visits in last 5 five weeks
    """

    patients = Patient\
        .objects\
        .filter(chw=chw)\
        .pregnant_months(period.start, period.end, 4.0, 9.5,\
            False, False)

    pregs = PregnancyReport\
        .objects\
        .filter(encounter__encounter_date__gt=\
                period.end - timedelta(10 * 30.4375),
            encounter__encounter_date__lte=\
                period.end,
            encounter__patient__in=patients)\
        .order_by('-encounter__encounter_date')

    seen = []
    no_anc = []
    women = []
    for p in pregs:
        if p.encounter.patient.pk in seen:
            continue
        else:
            seen.append(p.encounter.patient.pk)

        days_ago = (period.end - p.encounter.encounter_date).days
        weeks_ago = days_ago / 7.0
        months_ago = weeks_ago / 4.0

        preg_month = p.pregnancy_month + months_ago

        months_left = 9 - preg_month
        days_left = months_left * 30.475
        due_date = period.end + timedelta(days_left)

        # Current weeks since ANC
        if p.weeks_since_anc is None:
            no_anc.append((p.encounter.patient, \
                None,\
                due_date))
        else:
            weeks_since_anc = p.weeks_since_anc + weeks_ago
            if weeks_since_anc > 5.0:
                women.append((p.encounter.patient, \
                    p.encounter.encounter_date - \
                        timedelta(7 * p.weeks_since_anc), \
                    due_date))

    women.sort(lambda x,y: cmp(x[1],y[1]))
    return (no_anc + women)

def people_without_followup(period, chw):
    referrals = ReferralReport\
        .objects\
        .filter(encounter__chw=chw, \
            encounter__encounter_date__lte=period.end,\
            encounter__encounter_date__gte=period.start)\
        .exclude(urgency=ReferralReport.URGENCY_CONVENIENT)

    num_referrals = referrals.count()
    if num_referrals == 0:
        print "No referrals"
        return None

    ontime = []
    nofup = []
    for referral in referrals:
        rdate = referral.encounter.encounter_date
        try:
            fur = FollowUpReport.objects.filter(encounter__chw=chw, \
                        encounter__patient=referral.encounter.patient, \
                        encounter__encounter_date__gte=\
                            rdate+follow_up.DELTA_START_ON_TIME, \
                        encounter__encounter_date__lt=\
                            rdate+follow_up.DELTA_START_LATE)
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


def kids_needing_muac(period, chw):
    # people eligible for MUAC
    muac_list = Patient\
        .objects\
        .filter(chw=chw)\
        .muac_eligible(period.start, period.end)\
        .order_by('encounter__patient__location__code')

    seen = []
    need_muac = []
    no_muac = []

    one_month_ago = period.end - timedelta(30.4375)
    three_months_ago = period.end - timedelta(3*30.4375)

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
                .filter(encounter__patient__pk=p.pk,
                    muac__isnull=False,
                    status__isnull=False)\
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


