
from django.utils.translation import ugettext as _

from django.db.models.aggregates import Sum

from indicator import Indicator
from indicator import IndicatorPercentage
from indicator import QuerySetType

from childcount.models import Patient
from childcount.models.reports import FamilyPlanningReport
from childcount.models.FamilyPlanningUsage import FamilyPlanningUsage

def _fp_reports(period, data_in):
    return FamilyPlanningReport\
        .objects\
        .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))\
        .latest_for_patient()

def _sum_over_fps(period, data_in, field):
    return _fp_reports(period, data_in).aggregate(sum=Sum(field))['sum'] or 0

class Women(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "women"
    short_name  = _("# Women")
    long_name   = _("Total number of women seen "\
                    "during this period")

    @classmethod
    def _value(cls, period, data_in):
        return _sum_over_fps(period, data_in, 'women')

class Using(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "using"
    short_name  = _("# FP")
    long_name   = _("Total number of women seen "\
                    "during this period who are using "\
                    "modern family planning")

    @classmethod
    def _value(cls, period, data_in):
        return _sum_over_fps(period, data_in, 'women_using')

class UsingPerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)

    slug        = "using_perc"
    short_name  = _("% FP")
    long_name   = _("Percentage of women seen "\
                    "during this period who are using "\
                    "modern family planning")

    cls_num     = Using
    cls_den     = Women

def _using_fp_factory(code_in, slug_in, short_name_in, plural_in):
    class UsingClass(Indicator):
        type_in     = QuerySetType(Patient)
        type_out    = int

        slug        = None
        short_name  = None
        long_name   = None

        code        = None
        @classmethod
        def _value(cls, period, data_in):
            fps = _fp_reports(period, data_in)

            return FamilyPlanningUsage\
                .objects\
                .filter(fp_report__in=fps,\
                    method__code=cls.code)\
                .aggregate(sum=Sum('count'))['sum'] or 0

    UsingClass.code = code_in
    UsingClass.slug = "using_" + slug_in
    UsingClass.short_name = short_name_in 
    UsingClass.long_name = \
        _("Number of women seen during this period who are using "\
            "%s for family planning") % plural_in
    return UsingClass

UsingCondom = _using_fp_factory('c', 'condom', \
    _("Condom"), _("condoms"))
UsingInjectable = _using_fp_factory('i', 'injectable', \
    _("Injectable"), _("injectables"))
UsingIud = _using_fp_factory('iud', 'iud', \
    _("IUD"), _("IUDs"))
UsingImplant = _using_fp_factory('n', 'implant', \
    _("Implant"), _("implants"))
UsingPill = _using_fp_factory('p', 'pill', \
    _("Pill"), _("oral contraceptive pills"))
UsingSterilization = _using_fp_factory('st', 'sterilization', \
    _("Ster."), _("sterilization"))

class FpUsageChange(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = dict

    slug        = "fp_usage_change"

    @classmethod
    def _value(cls, period, data_in):
        starting = 0
        staying_on = 0
        ending = 0

        fps = _fp_reports(period, data_in)\
            .filter(women__isnull=False, women_using__isnull=False)\
            .iterator()

        for f in fps:
            try:
                latest = FamilyPlanningReport\
                    .objects\
                    .filter(encounter__patient=f.encounter.patient,
                        encounter__encounter_date__lt=f.encounter.encounter_date,
                        women__isnull=False,
                        women_using__isnull=False)\
                    .latest('encounter__encounter_date')
            except FamilyPlanningReport.DoesNotExist:
                starting += f.women_using
            else:
                starting += max(0, f.women_using - latest.women_using)
                staying_on += min(f.women_using, latest.women_using)
                ending += max(0, latest.women_using - f.women_using)

        return {
            'starting': starting,
            'staying_on': staying_on,
            'ending': ending,
        }

def _fp_change_factory(slug_in, short_name_in, long_name_in):
     
    class ChangeClass(Indicator):
        type_in     = QuerySetType(Patient)
        type_out    = int

        slug        = slug_in
        short_name  = short_name_in
        long_name   = _("Total number of women %s family planning "\
                        "during this period") % long_name_in

        @classmethod
        def _value(cls, period, data_in):
            return FpUsageChange(period, data_in)[cls.slug]

    return ChangeClass

Starting    = _fp_change_factory('starting', _('Starting'), _('starting'))
StayingOn   = _fp_change_factory('staying_on', _('Staying On'), _('staying on'))
Ending      = _fp_change_factory('ending', _('Ending'), _('ending'))

