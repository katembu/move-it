
from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models.reports import HouseHoldVisitReport
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
        response = ''
        created_by = self.message.persistant_connection.reporter.chw

        hhvr = HouseHoldVisitReport(created_by=created_by, patient=patient, \
                                    available=available)
        hhvr.save()
        if available:
            response = _('HH Member Available')
        else:
            response = _('HH Member NOT Available')

        return response
