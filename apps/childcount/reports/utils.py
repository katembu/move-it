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
        h = HTMLGenerator(doc, filename)
    elif rformat == 'xls':
        h = ExcelGenerator(doc, filename)
    elif rformat == 'pdf':
        h = PDFGenerator(doc, filename)
    else:
        raise ValueError('Invalid report format')

    print 'Rendering doc'
    h.render_document()
    print 'Done rendering'
    print filename
 
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
    print h.get_filename()

    shutil.move(h.get_filename(), report_filepath(filebasename, rformat))
    print "=== FINISHED IN %lg SECONDS ===" % (time.time() - tstart)
    return HttpResponseRedirect(report_url(filebasename, rformat))

def report_filepath(rname, rformat):
    return os.path.join(\
                    os.path.dirname(__file__), \
                    '..',
                    'static',
                    REPORTS_DIR,
                    rname+'.'+rformat)

def report_url(rname, rformat):
    return ''.join([\
        '/static/childcount/',
        REPORTS_DIR,'/',
        rname,'.',rformat
    ])
