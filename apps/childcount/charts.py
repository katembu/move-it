from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.barcharts import HorizontalBarChart, VerticalBarChart
from reportlab.lib import colors

mycolors =[colors.steelblue, colors.thistle, colors.cornflower, colors.lightsteelblue, colors.aquamarine, colors.cadetblue, colors.lightcoral, colors.tan, colors.darkseagreen, colors.lemonchiffon, colors.lavenderblush]

class CCBarChartDrawing(Drawing):
    def __init__(self, width=400, height=200, *args, **kw):
        Drawing.__init__(self, width, height, *args, **kw)
        self.add(VerticalBarChart(), name='chart')

        #set any shapes, fonts, colors you want here.  We'll just
        #set a title font and place the chart within the drawing
        self.chart.x = 20
        self.chart.y = 20
        self.chart.width = self.width - 20
        self.chart.height = self.height - 40
        self.chart.data = [[100,150,200,235]]


from reportlab.graphics.charts.piecharts import Pie

class CCPieChartDrawing(Drawing):
    def __init__(self, width=400, height=200, *args, **kw):
        Drawing.__init__(self,width,height,*args,**kw)
        self.add(Pie(), name='chart')
        self.chart.x = 75
        self.chart.y = 30
        self.chart.width = self.width - 150
        self.chart.height = self.height - 150
        self.chart.data = [10,20,30,40,50,60]
        self.chart.labels = ['a','b','c','d','e','f']
        self.chart.slices.strokeWidth = 0.5
       # self.chart.legend.defaultColors = mycolors

