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

def nightly_report_data(nrpt):
    rep = nrpt.report.get_definition()
    variants = rep.variants
    if len(variants) == 0:
        variants.append(('','',{}))
       
    data = {'obj':nrpt, 'variants':[]}
    for v in variants:
        rowdata = {
            'title': v[0],
            'formats': {},
        }
        for r in rep.formats:
            rowdata['formats'][r] = \
                {'filename': nrpt.get_filename(v[1], r),
                 'finished_at': nrpt.finished_at(v[1], r)}
        data['variants'].append(rowdata)
    return data
        


