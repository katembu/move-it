# Copyright(c) 2005-2007 Angelantonio Valente (y3sman@gmail.com)
# See LICENSE file for details.

""" PyRep's package """

# Configure logging subsystem
#import logging
#
#
#logging.basicConfig(level=logging.DEBUG,
#                    format='%(asctime)s %(levelname)-8s: %(message)s',
#                    datefmt='%a, %d %b %Y %H:%M:%S',
#                    filename='pyrep.log',
#                    filemode='w')

# Import names for simplify user imports

from base import *
from report import Report
from font import Font
from pdfrenderer import PDFRenderer
import dataproviders
from parser import XMLParser
