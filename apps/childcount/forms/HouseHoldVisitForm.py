
from django.utils.translation import ugettext_lazy as _

from childcount.forms import CCForm
from childcount.models.reports import HouseHoldVisitReport


class HouseHoldVisitForm(CCForm):
    KEYWORDS = {
        'en': ['n'],
    }

    def process(self, patient):
        if len(self.params) < 2:
            return False
        available = self.params[1]
        response = ''
        created_by = self.message.persistent_connection.reporter.chw

        if available.upper() == 'Y':
            available = True
        else:
            available = False
        hhvr = HouseHoldVisitReport(created_by=created_by, patient=patient, \
                                    available=available)
        hhvr.save()
        response = _('Visist registered to %(full_name)s. Thank you.') % \
                        patient.get_dictionary()
        return True
