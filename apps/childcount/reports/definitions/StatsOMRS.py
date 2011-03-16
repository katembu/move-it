
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

        t = Table(2, title=_t("Summary"))
        t.add_header_row([_t("Description"), _t("Value")])


        encounters = Encounter.objects.order_by('encounter_date')
        failed = encounters.filter(sync_omrs=False) 
        t.add_row([_t("Total Encounters"),
            Text(u"%d" % encounters.count())])
        t.add_row([_t("Encounters Sync'd"),
            Text(u"%d" % encounters.filter(sync_omrs=True).count())])
        t.add_row([_t("Encounters Failed"),
            Text(u"%d" % failed.count())])
        t.add_row([_t("Encounters Pending"),
            Text(u"%d" % encounters.filter(\
                Q(sync_omrs=None)|Q(sync_omrs__isnull=True)).count())])

        t2 = Table(4, title=_t("Failed Encounters"))
        t2.add_header_row([_t("Enc. Date"),\
            _t("Type"),\
            _t("Health ID"),\
            _t("Patient Name / Age")])

        t2.set_column_width(15, 0)
        t2.set_column_width(15, 1)
        t2.set_column_width(15, 2)

        for e in failed:
            type_str = filter(lambda t: t[0]==e.type,\
                Encounter.TYPE_CHOICES)[0][1]

            row = [e.encounter_date.strftime("%d-%b-%Y"),\
                type_str,
                e.patient.health_id.upper(),
                "%s / %s" % (e.patient.full_name(), \
                    e.patient.humanised_age())]
            t2.add_row(map(Text, row))

        doc.add_element(t)
        doc.add_element(t2)
        return render_doc_to_file(filepath, rformat, doc)

