import time

from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse

from rapidsms.webui.utils import render_to_response

from ccdoc import PDFGenerator, HTMLGenerator, ExcelGenerator

def render_doc_to_response(request, rformat, doc,
        filebasename = _(u'report'), append_date=True):
    tstart = time.time()
    h = None
    response = HttpResponse()

    if append_date:
        filebasename += time.strftime('%Y-%m-%d')

    # Don't cache the report
    response['Cache-Control'] = ''

    if rformat == 'html':
        h = HTMLGenerator(doc)
        response['Content-Type'] = 'text/html'
    elif rformat == 'xls':
        h = ExcelGenerator(doc)
        response['Content-Disposition'] = "attachment; " \
              "filename=\"%s.xls\"" % filebasename
        response['Content-Type'] = 'application/vnd.ms-excel'
    elif rformat == 'pdf':
        h = PDFGenerator(doc)
        response['Content-Disposition'] = "attachment; " \
              "filename=\"%s.pdf\"" % filebasename
        response['Content-Type'] = 'application/pdf'
    else:
        raise ValueError('Invalid report format')

    h.render_document()
    response.write(h.get_contents())
    print "=== FINISHED IN %lg SECONDS ===" % (time.time() - tstart)
    return response

