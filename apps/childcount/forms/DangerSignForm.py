from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models.reports import DangerSignReport
from childcount.models import DangerSign
from childcount.exceptions import ParseError


class DangerSignForm(CCForm):
    KEYWORDS = {
        'en': ['ds'],
    }

    def process(self, patient):
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info, expected (%s) danger signs") % \
                            self.PREFIX)
        response = ''
        created_by = self.message.persistant_connection.reporter.chw

        rp = DangerSignReport(created_by=created_by, \
                            patient=patient)
        rp.save()

        danger_signs = dict([(danger_sign.code, danger_sign) \
                             for danger_sign in \
                             DangerSign.objects.filter(type='dangersign') ])
        observed = []
        print self.params
        text = ''
        for d in self.params[1:]:
            obj = danger_signs.get(d.upper(), None)
            if obj is not None:
                observed.append(obj)
                text += obj.description
        for danger_sign in observed:
            rp.danger_signs.add(danger_sign)
        rp.save()
        if len(text) > 1:
            response += '(' + text + ')'
        else:
            response = _(u"Unknown danger signs %s " % ','.join(self.params[1]))

        return response
