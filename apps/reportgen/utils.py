import os
import os.path
import shutil
import json 

from datetime import datetime

from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.http import HttpResponse

from reportgen.models import Report
from reportgen.timeperiods import PERIOD_TYPES

from ccdoc import PDFGenerator, HTMLGenerator, ExcelGenerator

"""
The maximum number of generated reports to display
on the on-demand reports page.
"""
DISPLAY_REPORTS_MAX = 30

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

def ondemand_json_obj():
    rall = Report.objects.order_by('title')
    rpts = {}
    variants = {}
    formats = {}
    for r in rall:
        d = r.get_definition()

        rpts[r.pk] = r.title
        variants[r.pk] = {}
        for v in d.variants:
            # Index by the variant filename suffix
            variants[r.pk][v[1]] = v[0]
            
        formats[r.pk] = {}
        for f in d.formats:
            formats[r.pk][f] = f.upper()

    time_types = {}
    time_periods = {}
    for pt in PERIOD_TYPES:
        time_types[pt.code] = pt.title
        time_periods[pt.code] = {}
        for i,p in enumerate(pt.periods()):
            time_periods[pt.code][i] = p.title


    return json.dumps({
        'rpts': rpts,
        'variants': variants,
        'formats': formats,
        'time_types': time_types,
        'time_periods': time_periods,
    })

def file_size(filepath):
    return os.path.getsize(filepath) 
