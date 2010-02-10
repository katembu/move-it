from django.utils.translation import ugettext_lazy as _

from childcount.forms import CCForm
from childcount.models import CHW, Referral
from childcount.models.reports import HealthReport


class HealthStatusForm(CCForm):
    KEYWORDS = {
        'en': ['h'],
    }

    def process(self, patient):
        if len(self.params) < 3:
            return False
        visited_clinic = self.params[1]
        danger_signs = self.params[2]
        response = ''
        created_by = self.message.persistent_connection.reporter.chw

        if visited_clinic in HealthReport.VISITED_CLINIC_CHOICES \
            and danger_signs in HealthReport.DANGER_SIGNS_CHOICES:
            if danger_signs == HealthReport.DANGER_SIGNS_PRESENT:
                rf = Referral(created_by=created_by, patient=patient)
                rf.save()
                response = _('Danger signs present')
            hr = HealthReport(created_by=created_by, patient=patient, \
                         visited_clinic=visited_clinic, danger_signs=danger_signs)
            hr.save()
        return response
