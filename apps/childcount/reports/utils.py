import time
import os
import shutil

from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse

from rapidsms.webui.utils import render_to_response

from ccdoc import PDFGenerator, HTMLGenerator, ExcelGenerator

REPORTS_DIR = 'reports'

def render_doc_to_file(filename, rformat, doc):
    h = None 

    if rformat == 'html':
        h = HTMLGenerator(doc)
    elif rformat == 'xls':
        h = ExcelGenerator(doc)
    elif rformat == 'pdf':
        h = PDFGenerator(doc)
    else:
        raise ValueError('Invalid report format')

    h.render_document()
    return shutil.move(h.get_filename(), filename)
 
def render_doc_to_response(request, rformat, doc,
        filebasename = _(u'report')):
    tstart = time.time()
    h = None

    if rformat == 'html':
        h = HTMLGenerator(doc)
    elif rformat == 'xls':
        h = ExcelGenerator(doc)
    elif rformat == 'pdf':
        h = PDFGenerator(doc)
    else:
        raise ValueError('Invalid report format')

    h.render_document()
    filename = filebasename + '.' + rformat
    print h.get_filename()

    shutil.move(h.get_filename(), report_filename(filename))
    print "=== FINISHED IN %lg SECONDS ===" % (time.time() - tstart)
    return HttpResponseRedirect( \
        '/static/childcount/' + REPORTS_DIR + '/' + filename)

def report_filename(report_name):
    return os.path.abspath(\
        os.path.join(
                    os.path.dirname(__file__), \
                    '..',
                    'static',
                    REPORTS_DIR,
                    report_name))

