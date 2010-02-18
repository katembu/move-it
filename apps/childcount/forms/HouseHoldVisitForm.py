
from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models.reports import HouseHoldVisitReport
from childcount.models import DangerSign
from childcount.forms.utils import MultipleChoiceField
from childcount.exceptions import ParseError


class HouseHoldVisitForm(CCForm):
    KEYWORDS = {
        'en': ['v'],
    }

    available_field = MultipleChoiceField()
    available_field.add_choice('en', True, 'Y')
    available_field.add_choice('en', False, 'N')

    def process(self, patient):
        self.available_field.set_language(self.message.reporter.language)
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info, expected (%s)") % \
                            ('/'.join(self.available_field.valid_choices())))
        if not self.available_field.is_valid_choice(self.params[1]):
            raise ParseError(_(u"HH Member Available choices must be "\
                               "%(choices)s") % \
                              {'choices': self.available_field.choices_string()})
        available = self.available_field.get_db_value(self.params[1])
        
        if available:
            if len(self.params) < 4:
                raise ParseError(_(u"Not enough info, expected (%s) (number "\
                               "of pregnant) (number_of_under_five)") % \
                            ('/'.join(self.available_field.valid_choices())))
            if not self.params[2].isdigit():
                raise ParseError(_("Wrong value for number of pregnant women,"\
                                   " expected a number"))
            if not self.params[3].isdigit():
                raise ParseError(_("Wrong value for number of under five,"\
                                   " expected a number"))
        created_by = self.message.persistant_connection.reporter.chw

        if not available:
            hhvr = HouseHoldVisitReport(created_by=created_by, \
                                        patient=patient, available=available)
            hhvr.save()
            response = _("HH Member NOT Available")
        else:
            hhvr = HouseHoldVisitReport(created_by=created_by, \
                                        patient=patient, available=available)
            hhvr.pregnant = int(self.params[2])
            hhvr.underfive = int(self.params[3])
            hhvr.save()

            danger_signs = dict([(danger_sign.code, danger_sign) \
                             for danger_sign in DangerSign.objects.all() ])
            observed = []
            print self.params
            text = []
            for d in self.params[4:]:
                obj = danger_signs.get(d.upper(), None)
                if obj is not None:
                    observed.append(obj)
                    text.append(obj.description)
            for danger_sign in observed:
                hhvr.danger_signs.add(danger_sign)
            hhvr.save()
            self.response = _("HH Member Available, %(pregnant)s pregnant, "\
                         "%(underfive)s underfive, "\
                         "Activities(%(activities)s).") % \
                         {'pregnant': hhvr.pregnant, \
                                              'underfive': hhvr.underfive, \
                                              'activities': ','.join(text)}
