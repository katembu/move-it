from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models.reports import DispensationReport
from childcount.models import Commodity
from childcount.exceptions import ParseError


class DispensationForm(CCForm):
    KEYWORDS = {
        'en': ['g'],
    }

    def process(self, patient):
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info, expected at least one "\
                               "commodity"))
        response = ''
        created_by = self.message.persistant_connection.reporter.chw

        commodities = dict([(commodity.code, commodity) \
                             for commodity in Commodity.objects.all() ])
        observed = []
        print self.params
        text = ''
        unknown = []
        for issue in self.params[1:]:
            obj = commodities.get(issue.upper(), None)
            if obj is not None:
                observed.append(obj)
                text += obj.description
            else:
                unknown.append(issue)

        if len(text) > 1 and len(observed) > 0:
            rp = DispensationReport(created_by=created_by, \
                            patient=patient)
            rp.save()
            for commodity in observed:
                rp.commodities.add(commodity)
            rp.save()
            response += 'dispensed(' + text + ')'
        if len(unknown) > 0:
            response += 'unknown(' + ', '.join(unknown) + ')'

        return response
