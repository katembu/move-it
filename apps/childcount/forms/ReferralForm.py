from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models.reports import ReferralReport
from childcount.exceptions import ParseError
from childcount.forms.utils import MultipleChoiceField



class ReferralForm(CCForm):
    KEYWORDS = {
        'en': ['r'],
    }

    urgency_field = MultipleChoiceField()
    urgency_field.add_choice('en', ReferralReport.URGENCY_AMBULANCE, 'A')
    urgency_field.add_choice('en', ReferralReport.URGENCY_BASIC, 'B')
    urgency_field.add_choice('en', ReferralReport.URGENCY_CONVENIENT, 'C')

    def process(self, patient):
        self.urgency_field.set_language(self.message.reporter.language)
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info, expected (%s)") % \
                            ('/'.join(self.urgency_field.valid_choices())))
        response = ''
        created_by = self.message.persistant_connection.reporter.chw
        if not self.urgency_field.is_valid_choice(self.params[1]):
            raise ParseError(_(u"Referral in clinic options are %(choices)s") \
                             % \
                            {'choices': self.available_field.choices_string()})
        urgency = self.urgency_field.get_db_value(self.params[1])

        if urgency == ReferralReport.URGENCY_AMBULANCE:
            response = _('Ambulance Referral')
        if urgency == ReferralReport.URGENCY_BASIC:
            response = _('Basic Referral(24hrs)')
        if urgency == ReferralReport.URGENCY_CONVENIENT:
            response = _('Convenient Referral')
        rp = ReferralReport(created_by=created_by, urgency=urgency, \
                            patient=patient)
        rp.save()

        return response
