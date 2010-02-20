from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models.reports import ReferralReport
from childcount.exceptions import ParseError
from childcount.forms.utils import MultipleChoiceField


class ReferralForm(CCForm):
    KEYWORDS = {
        'en': ['r'],
    }

    def process(self, patient):
        chw = self.message.persistant_connection.reporter.chw

        urgency_field = MultipleChoiceField()
        urgency_field.add_choice('en', ReferralReport.URGENCY_AMBULANCE, 'A')
        urgency_field.add_choice('en', ReferralReport.URGENCY_EMERGENCY, 'E')
        urgency_field.add_choice('en', ReferralReport.URGENCY_BASIC, 'B')
        urgency_field.add_choice('en', ReferralReport.URGENCY_CONVENIENT, 'C')
        urgency_field.set_language(chw.language)
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info, expected %s") % \
                              urgency_field.choices_string())

        if not urgency_field.is_valid_choice(self.params[1]):
            raise ParseError(_(u"Referral to clinic choices are %(choices)s") \
                             % {'choices': urgency_field.choices_string()})

        urgency = urgency_field.get_db_value(self.params[1])

        if urgency == ReferralReport.URGENCY_AMBULANCE:
            self.response = _(u"Ambulance Referral")
        if urgency == ReferralReport.URGENCY_EMERGENCY:
            self.response = _(u"Emergency Referral")
        if urgency == ReferralReport.URGENCY_BASIC:
            self.response = _(u"Basic Referral(24hrs)")
        if urgency == ReferralReport.URGENCY_CONVENIENT:
            self.response = _(u"Convenient Referral")

        rp = ReferralReport(created_by=chw, urgency=urgency, \
                            patient=patient)
        rp.save()
