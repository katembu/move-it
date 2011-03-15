
from django.db.models import Q
from django.utils.translation import gettext as _ 

from ccdoc import Document, Table, Paragraph, Text

from childcount.models import Encounter
from childcount.reports.report_framework import PrintedReport
from childcount.reports.utils import render_doc_to_file

class Report(PrintedReport):
    title = _('OpenMRS Sync Data')
    filename = 'stats_omrs'
    formats = ['pdf','xls','html']

    def generate(self, rformat, title, filepath, data):
        def _t(string):
            return Text(_(unicode(string)))

        doc = Document(self.title, '')

        t = Table(2)
        t.add_header_row([_t("Description"), _t("Value")])

        encounters = Encounter.objects.all()
        t.add_row([_t("Total Encounters"),
            Text(u"%d" % encounters.count())])
        t.add_row([_t("Encounters Sync'd"),
            Text(u"%d" % encounters.filter(sync_omrs=True).count())])
        t.add_row([_t("Encounters Failed"),
            Text(u"%d" % encounters.filter(sync_omrs=False).count())])
        t.add_row([_t("Encounters Pending"),
            Text(u"%d" % encounters.filter(\
                Q(sync_omrs=None)|Q(sync_omrs__isnull=True)).count())])
        doc.add_element(t)

        return render_doc_to_file(filepath, rformat, doc)

