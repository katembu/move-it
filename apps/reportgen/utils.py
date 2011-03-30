import os
import os.path
import shutil

from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _
from django.http import HttpResponse

from ccdoc import PDFGenerator, HTMLGenerator, ExcelGenerator

def render_doc_to_file(filename, rformat, doc):
    h = None 

    if rformat == 'html':
        h = HTMLGenerator(doc, filename)
    elif rformat == 'xls':
        h = ExcelGenerator(doc, filename)
    elif rformat == 'pdf':
        h = PDFGenerator(doc, filename)
    else:
        raise ValueError(_("Invalid report format (%s)") % rformat)

    print 'Rendering doc'
    h.render_document()
    print 'Done rendering'
    print filename

def report_filepath(rdir, rname, rformat):
    return os.path.join(\
                    os.path.dirname(__file__), \
                    'static',
                    rdir, rname+'.'+rformat)

def report_modified_on(rdir, rname, rformat):
    fname = report_filepath(rdir, rname, rformat)
    if not os.path.exists(fname):
        return None
    return datetime.fromtimestamp(os.path.getmtime(fname))

def report_url(rdir, rname, rformat):
    return ''.join([\
        '/static/reportgen/',
        rdir,'/', rname,'.',rformat
    ])
