# Import document elements
from ccdoc.document import Document
from ccdoc.paragraph import Paragraph
from ccdoc.section import Section
from ccdoc.text import Text
from ccdoc.table import Table
from ccdoc.hline import HLine

# Import generators
from ccdoc.html import HTMLGenerator
from ccdoc.excel import ExcelGenerator
from ccdoc.pdf import PDFGenerator

doc = Document(title=u'My Title', subtitle=u'My Subtitle')

doc.add_element(Section(u'First Section'))
doc.add_element(
    Paragraph([ 
        Text(u'One normal sentence. '), 
        Text(u'One bold sentence. ', bold=True), 
        Text(u'One italic sentence.', italic=True) 
        ]))
doc.add_element(HLine())

doc.add_element(Section(u'Second Section'))

tab = Table(3, title=Text(u'My Great Table'))
tab.add_header_row([ 
    Text(u'First Col'),
    Text(u'Second Col'), 
    Text(u'Third Col')])
tab.add_header_row([ 
    Text(u'First Cell'),
    Text(u'Second Cell'), 
    Text(u'Third Cell')])
doc.add_element(tab)

# Create a new generator for this Document
gen = HTMLGenerator(doc)

gen.render_document()
print gen.get_contents()

# End of example


