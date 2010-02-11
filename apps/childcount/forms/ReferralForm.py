from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models.reports import ReferralReport




class Referral(CCForm):
    KEYWORDS = {
        'en': ['h'],
    }

    def process(self, patient):
        if len(self.params) < 2:
            return False
        response = ''
        created_by = self.message.persistent_connection.reporter.chw
        urgency = self.params[1]
        
        if urgency in ReferralReport.URGENCY_CHOICES:
            if urgency == ReferralReport.URGENCY_AMBULANCE:
                response = _('Ambulance Referral')
            if urgency == ReferralReport.URGENCY_BASIC:
                response = _('Basic Referral(24hrs)')
            if urgency == ReferralReport.URGENCY_CONVENIENT:
                response = _('Convenient Referral')
            #TODO create danger signs and save the report
 
        return response
