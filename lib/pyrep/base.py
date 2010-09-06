# Copyright(c) 2005-2007 Angelantonio Valente (y3sman@gmail.com)
# See LICENSE file for details.

""" 
Base classes.

This module defines the classes to use to build a report.

Millimeters is the default unit of measurement.
"""

import copy
import datetime
import decimal
import random
import time
import locale

import dataproviders
import font

def mm(*values):
    """
    Returns the given values in millimeters (does nothing, since mm is the default)
    """
    if len(values) == 1:
        return values[0]
    return values

def cm(*values):
    """
    Returns the given values converted in millimeters from centimeters
    """
    if len(values) == 1:
        return values[0] * 10
    return tuple([x * 10 for x in values])

def quote(value):
    return "\"\"\"%s\"\"\""%value
    
# Supported units
units={
    'mm':mm,
    'cm':cm,
    '':mm,
}

class ReportError(StandardError):
    """
    Exception
    """

class Size(object):
    """
    Encapsulate a size as a width, height tuple.
    """
    
    def __init__(self, *args):
        
        if len(args) == 1:
            args = args[0]
            
        if len(args) != 2:
            raise ReportError("Wrong size spec: %s"%args)

        self.width, self.height = args
        
    def __len__(self):
        return 2
        
    def __getitem__(self, item):
        return (self.width, self.height)[item]
    
    def __setitem__(self, item, value):
        if item == 0:
            self.width = value
        elif item == 1:
            self.height = value
        else:
            raise IndexError("Index out of range: %s"%item)
    
    def __sub__(self, value):
        try:
            value + 0
            0 - value
            
            w = self.width - value
            h = self.height - value
            
            return self.__class__(w, h)
        except StandardError, e:
            try:
                w = self.width - value[0]
                h = self.height - value[1]
                
                return self.__class__(w, h)
            except StandardError, e:
                raise ValueError("Invalid value for sub: %s"%value)
                
    def __str__(self):
        return "Size(%s, %s)"%(self.width, self.height)
    
    def __eq__(self, value):
        if isinstance(value, Size):
            return True
        return (self.width == value[0]) and (self.height == value[1])
            
class Color(object):
    """
    Object's color in RGB form
    @ivar red: Red component in decimal 0-255 range
    @ivar green: Green component in decimal 0-255 range
    @ivar blue: Red component in decimal 0-255 range
    """

    class _ColorMetaClass(type):
        """
        Used to add constants to the class
        """
        
        defaults = {
                  'BLACK': (0, 0, 0),
                  'WHITE': (255, 255, 255),
                  'RED': (255, 0, 0),
                  'GREEN': (0, 255, 0),
                  'BLUE': (0, 0, 255),
                  }
        
        def __new__(cls,classname,bases,classdict):
            c = type.__new__(cls, classname, bases, classdict)
            
            for k, v in cls.defaults.items():
                setattr(c, k, c(*v))

            return c
    
    __metaclass__ = _ColorMetaClass
    
    def __init__(self, red, green, blue):
        """
        Constructor
        @param red: Red component in decimal 0-255 range
        @param green: Green component in decimal 0-255 range
        @param blue: Blue component in decimal 0-255 range
        """

        for x in ("red", "green", "blue"):
            v = locals()[x]

            if v<0 or v>255:
                raise ReportError("Invalid value for %s component: %s (must be in range 0 - 255)"%(x,v))
        
        self.red = red
        self.green = green
        self.blue = blue
        
    def to_hex(self):
        """
        Converts the color values to hex (web) format
        """
        
        ret = ["#"]
        
        for x in (self.red, self.green, self.blue):
            c = "%X"%x
            if len(c) == 1: c = "0%s"%c
            ret.append(c)
            
        return "".join(ret)
    
    @classmethod
    def from_hex(cls, hexvalue):
        """
        Create a color object from an hex-encoded string (eg. #AABBCC)
        """
        if hexvalue[0] == "#":
            hexvalue = hexvalue[1:]

        rgb = hexvalue + ('0' * (6 - len(hexvalue)))
        
        r = int(rgb[0: 2], 16)
        g = int(rgb[2: 4], 16)
        b = int(rgb[4: 6], 16)
        
        return cls(r, g, b)
        
    def __str__(self):
        """
        If this is a default colour, returns its name, else the tuple (red, green, blue)
        """
        for k, c in self.__metaclass__.defaults.items():
            if self == Color(*c):
                return "Color.%s"%k
            
        return "(%s, %s, %s)"%(self.red, self.green, self.blue)
    
    def __eq__(self, color):
        return self.red == color.red and self.green == color.green and self.blue == color.blue

    def __len__(self):
        """
        The length of the colour when considered as a sequence is always 3: (r, g, b)!
        """
        return 3
        
    def __getitem__(self, item):
        """
        By defining this (and __len__) you can get the tuple of (r, g, b) in an easy way: just do tuple(color)!
        """
        return (self.red, self.green, self.blue)[item]
    
    @classmethod
    def random(cls):
        """
        Returns a random color
        """
        r, g, b = (random.randint(0, 255) for x in range(3))
        return cls(r, g, b)
        
class DrawableObject(object):
    """
    Base class for drawable objects. A drawable object knows its size and how to draw itself.
    @ivar color: Object's foreground color
    @ivar backcolor: Object's background color
    """
    
    def __init__(self, size, **kwargs):
        """
        Constructor
        @param parent: The parent section
        @param size: Object's size (as a sequence of width, height)
        @param position: Object's position (as a sequence of x, y)
        @param color: Object's foreground color
        @param backcolor: Object's background color
        """
        
        self._size = Size(0, 0)
        self._position = (0, 0)
        
        self.parent = kwargs.get('parent', None)

        self.size = Size(size)
        self.position = kwargs.get('position', (0, 0))
        
        self.color = kwargs.get('color', Color.BLACK)
        self.backcolor = kwargs.get('backcolor', Color.WHITE)
            
    def check_tuple(self, t):
        """
        Returns the two-items iterable t as a touple
        @param t: An object that supports unpacking
        @returns: A Tuple with the two elements of t
        """
        
        w, h = t
        return (w, h)
    
    def set_size(self, size):
        """
        Sets the object's size
        @param size: A two items iterable
        @raise ReportError: Exception raised if the size isn't correct
        """
        
        size = list(self.check_tuple(size))

        if self.parent is not None:
            if self.size[0] + self.x > self.parent.size[0]:
                raise ReportError("Child %s exceed parent's width (parent: %s, child: %s + %s)!"%(self, self.parent.size[0], self.x, self.size[0]))
    
            if self.size[1] + self.y > self.parent.size[1]:
                raise ReportError("Child %s exceed parent's height (parent: %s, child: %s + %s)!"%(self, self.parent.size[1], self.y, self.size[1]))

        self._size = Size(tuple(size))
        
    def get_size(self):
        """
        Returns the object's size
        @returns: A (width, height) tuple
        """
        
        size = list(self._size)
        for i in (0, 1):
            if size[i] is None and self.parent is not None:
                size[i] = self.parent.size[i]
            elif size[i] < 0 and self.parent is not None:
                size[i] = self.parent.size[i] + size[i]
        return Size(tuple(size))
    
    def set_position(self, position):
        """
        Sets the object's position
        @param position: The position to set
        """
        
        self._position = self.check_tuple(position)

    def draw(self, renderer, environment = None):
        """
        Ask the renderer to draw ourself
        @param renderer: A renderer object
        @param environment: The environment data
        """
        
        raise NotImplementedError("Please use a subclass!")

    def set_x(self, x):
        self.position = (x, self.position[1])
    
    def set_y(self, y):
        self.position = (self.position[0], y)

    def set_width(self, w):
        self.size = Size(w, self.height)
        
    def set_height(self, h):
        self.size = Size(self.width, h)
    
    def __str__(self):
        return "<%s> size (%s, %s), pos (%s, %s)"%(self.__class__.__name__, self.width, self.height, self.x, self.y)
        
    size = property(get_size, set_size, None, """ Object's size """)
    position = property(lambda self: self._position, set_position, None, """ Object's position """)
    width = property(lambda self: self.size[0], set_width, None, """ Object's width """ )
    height = property(lambda self: self.size[1], set_height, None, """ Object's height """ )
    x = property(lambda self: self.position[0], set_x, None, """ Object's x position """)
    y = property(lambda self: self.position[1], set_y, None, """ Object's y position """)
    
class Container(DrawableObject):
    """
    An object that contains one or more children
    @ivar children: A list of the object's children 
    @ivar default_font: The default font for this container (used if children don't have an explicit font)
    @type default_font: Font object
    """
    
    def __init__(self, size, **kwargs):
        """
        Constructor
        @param size: Object's size
        @keyword default_font: The object's default font.
        """
        
        super(Container, self).__init__(size, **kwargs)
        
        self.children = list()
        
        self.default_font = kwargs.get("default_font", font.Font("default", "Helvetica", 10))
        
    def add_child(self, position, child):
        """
        Adds a child to this container
        @param position: The child's position
        @param child: The child object. It must expose the "draw" method
        """
        
        if not hasattr(child, 'draw') or not callable(getattr(child, 'draw')): 
            raise ReportError("Child object is not drawable: %s"%child)
        
        x, y = child.check_tuple(position)

        child.parent = self

        if child.size[0] + x > self.size[0]:
            raise ReportError("Child %s exceed parent's width (parent: %s, child: %s + %s)!"%(child, self.size[0], x, child.size[0]))

        if child.size[1] + y > self.size[1]:
            raise ReportError("Child %s exceed parent's height (parent: %s, child: %s + %s)!"%(child, self.size[1], y, child.size[1]))
        
        child.position = position
        self.children.append(child)
    
    def get_font(self, name):
        return self.parent.get_font(name)
             
    def draw(self, renderer, environment = None):
        """
        Draws each child using the given renderer and environment
        @param renderer: The renderer that will actually draw the children
        @type renderer: A Renderer subclass
        @param environment: The environment data to use
        """
        for child in self.children:
            child.draw(renderer, environment)
            
class Page(DrawableObject):
    """
    Page definition
    @cvar standard_pages: A mapping of standard page sizes. The key is the standard name, the value is a tuple of (width, height)
    @cvar user_defined_pages: A Mapping of user defined page sizes
    @ivar margins: The non-drawable page margins
    """
    
    standard_pages={
                    'A4': (210,297),
                    'Letter': (210, 279),
                    }
    
    user_defined_pages={}
    
    def __init__(self, size = 'A4'):
        """
        Constructor
        @param size: Page size (as a tuple or as a standard page name: eg. A4, Letter)
        """
        self.set_size(size)
        
        self.margins=[0,0,0,0]
        
    def set_size(self, size):
        """
        Sets the page's size
        @param size: A ISO page size name (like A4, Letter, etc.) or a (width, height) tuple
        """
        
        s = None
        try:
            s = self.__class__.standard_pages[size]
        except KeyError:
            try:
                s = self.__class__.user_defined_pages[size]
            except KeyError:
                pass
        
        if s is None:
            try:
                width = s[0]+0
                height = s[1]+0
            except:
                raise
        else:
            width, height = s
            
        self._size = (width, height)
    
    size = property(lambda self: self._size, None, None)
    
    @classmethod
    def add_userdefined_pagesize(cls, name, size):
        """
        Adds an user-defined page size to the pages registry
        @param name: Page size's name
        @param size: (width, height) tuple
        """
        cls.user_defined_pages[name] = size
        
class Picture(DrawableObject):
    """
    An image - TO DEFINE
    """
    
class Text(DrawableObject):
    """
    A Text value, used to display any kind of textual value
    @ivar font: The object's font
    @type font: Font
    @ivar value: The object's value. Could be any valid python expression that will be (safely, we hope) evaluated on runtime. You cannot use "dangerous" 
                 functions as the value, unless you define your custom functions
    @type value: string
    @ivar alignment: Text alignment in the field
    @type alignment: One of ALIGN_LEFT, ALIGN_RIGHT, ALIGN_CENTER
    """
    
    ALIGN_LEFT = 0
    ALIGN_CENTER = 1
    ALIGN_RIGHT = 2
    
    def __init__(self, size, **kwargs):
        """
        Constructor
        @param size: The field's size as a tuple of (width, height)
        @keyword font: Object's font
        @keyword value: Object's value (a valid python expression to be evaulated)
        @keyword alignment: one of ALIGN_LEFT, ALIGN_CENTER, ALIGN_RIGHT: Aligns the text in the field
        @keyword color: Text color
        @keyword stretch: TO DOCUMENT
        """
        
        super(Text,self).__init__(size, **kwargs)
        
        self.font = kwargs.get('font', None)
        if isinstance(self.font, basestring):
            self.font = self.parent.get_font(self.font)
        
        self.value = kwargs.get('value', "")
        
        self.alignment = kwargs.get('alignment', self.__class__.ALIGN_LEFT)
        
        self.color = kwargs.get('color', None)
    
    def draw(self, renderer, environment = None):
        """
        Draws the component using the given renderer
        """
        if self.font is None:
            self.font = self.parent.default_font
            
        renderer.draw_text(self, environment)
    
    def __str__(self):
        return "Text object: %s"%self.value
    
class Shape(DrawableObject):
    """ 
    Base class for shapes
    @ivar linewidth: Line width in millimeters
    @ivar linetype: The line' shape. By now you can only make solid lines    
    """
    SOLID = 1

    def __init__(self, size, linewidth = 0.5, linetype = SOLID, linecolor = Color.BLACK):
        super(Shape, self).__init__(size)
        
        self.linewidth = linewidth
        self.linetype = linetype
        
        self.color = linecolor
        
class HLine(Shape):
    """ Horizontal line """

    def __init__(self, width = None, linewidth = 0.2, linetype = Shape.SOLID, linecolor = Color.BLACK):
        """
        Constructor
        @param width: Line's width on the page, expressed in millimeters. If None, the container's width will be used
        @param linewidth: The line's width (defaults to 0.2 millimeters)
        @param linetype: The line's type. By now, only solid lines are supported
        """
        
        super(HLine, self).__init__( (width, 0), linewidth, linetype, linecolor)

    def draw(self, renderer, environment = None):
        renderer.draw_hline(self, environment)
        
class VLine(Shape):
    """ Vertical line """

    def __init__(self, height = None, linewidth = 0.2, linetype = Shape.SOLID, linecolor = Color.BLACK):
        """
        Constructor
        @param height: Line's height on the page, expressed in millimeters. If None, the container's height will be used
        @param linewidth: The line's width (defaults to 0.2 millimeters)
        @param linetype: The line's type. By now, only solid lines are supported
        """
        super(VLine, self).__init__( (0, height), linewidth, linetype, linecolor)

    def draw(self, renderer, environment = None):
        renderer.draw_vline(self, environment)
    
class Box(Shape):
    """ A Box """

    def __init__(self, size, linewidth = 0.2, linetype = Shape.SOLID, bordercolor = Color.BLACK, fillcolor = None, round = 0):
        super(Box, self).__init__( size, linewidth, linetype, bordercolor)

        self.backcolor = fillcolor
        
        self.round = round

    def draw(self, renderer, environment = None):
        renderer.draw_box(self, environment)

class Section(Container):
    """ A Report's section """
    
    def __init__(self, parent, size, **kwargs):
        kwargs['parent'] = parent
        super(Section, self).__init__(size, **kwargs)
    
    def set_size(self, size):
        """
        We need to do additional tests on sections's size, e.g. if the total height 
        of header+body+footer exceeds page's height. Leave that tests to the 
        report itself
        """
        
        # TODO: do we need to reduce coupling between section and report?
        
        self.parent.check_sections_height()
        
        super(Section, self).set_size(size)        
    
    def get_size(self):
        """
        Look at DrawableObject's get_size!
        """
        return super(Section, self).get_size()
        
    size = property(get_size, set_size, None, """ Section's size """)
    
    def __getattr__(self, attr):
        """
        We return section's name as the real name. This is a little bit tricky...
        """
        
        if attr == 'name':
            return {
                self.parent.header : "Header",
                self.parent.title : "Title",
                self.parent.body : "Body",
                self.parent.footer : "Footer",
                self.parent.summary : "Summary",
            }.get(self, "Section")
        
        return super(Section, self).__getattr__(attr)
        
class Group(object):
    """
    Data groups - NOT IMPLEMENTED
    """
    
    def __init__(self, name, expression):
        self.name = name
        self.expression = expression
        
        self.header = Section(self, (0,0))
        self.footer = Section(self, (0,0))

class Data(object):
    """
    TODO: TO DOCUMENT
    """
    class _Object(object):
        pass
    
    def __init__(self, report):
        self.report = report
        
    def get_data(self):
        """
        Returns valid data
        """
        
        def format_date(date, loc = None):
            return date.strftime(locale.nl_langinfo(locale.D_FMT))
        
        def iif(cond, val1, val2):
            if cond:
                return val1
            else:
                return val2
                
        import __builtin__

        # System variables
        system = self.__class__._Object()
        system.page = self.report.pagenum     # Current page number
        system.date = datetime.date.today()

        # User-defined variables
        vars = self.__class__._Object()
        for name, val in self.report.variables.items():
            setattr(vars, name, val.value)

        # Report parameters
        parameters = self.__class__._Object()
        for name, val in self.report.parameters.items():
            setattr(parameters, name, val.value)
            
        # System functions
        funcs = self.__class__._Object()
        # Builds a "safe" functions dict
        valid_names = ('abs', 'bool', 'chr', 'cmp', 'divmod', 'float', 'hash', 
                       'hex', 'int', 'len', 'max', 'min', 'oct', 'ord', 'pow',
                       'range', 'round', 'str', 'sum', 'unichr', 'unicode',
                       )
        
        local_names = ('format_date', 'iif')
        
        for name in valid_names:
            setattr(funcs, name, getattr(__builtin__, name))
        
        for name in local_names:
            setattr(funcs, name, locals()[name])
        
        # Current datasource row
        row = self.report.currentrow
                
        d = dict()
        for n in ('system', 'vars', 'row', 'funcs'):
            d[n] = locals()[n]
            
        return d
                    
class Renderer(object):
    """
    Base renderer class
    """
    
    def __init__(self, report):
        """
        Constructor
        @param report: The Report object to render
        """
        
        self.report = report

    def render(self, *args, **kwargs):

        # Data sources
        self.datasources = kwargs.get('datasources', None)
        if self.datasources is None:
            if self.report.datasources:
                self.datasources = []
                if "main" in self.report.datasources:
                    self.datasources.append(self.report.datasources['main'])
                    
                for name, ds in self.report.datasources.items():
                    if name != 'main':
                        self.datasources.append(ds)

            
        if not self.datasources:
            self.datasources = [dataproviders.DataProvider([1])]

        # Main datasource
        self.maindatasource = kwargs.get('maindatasource', self.datasources[0])
        
        for ds in self.datasources:
            dargs = {}
            for arg in kwargs:
                if arg in ("conn", "module", "conn_pars"):
                    dargs[arg] = kwargs[arg]
            ds.run(**dargs)
        
    def start_page(self):
        pass
    
    def finalize_page(self):
        pass
    
    def draw_text(self, text, environment = None):
        raise NotImplementedError("Please use a subclass!")

    def draw_vline(self, shape, environment = None):
        raise NotImplementedError("Please use a subclass!")

    def draw_hline(self, shape, environment = None):
        raise NotImplementedError("Please use a subclass!")

    def draw_box(self, shape, environment = None):
        raise NotImplementedError("Please use a subclass!")
    
    def safe_eval(self, expr, environment):
        """
        Safely evaluates the expression "expr"
        @param expr: The expression to be evaluated
        @param environment: The environment object to use
        @returns: the evaluated value
        @raises: ReportError if the expression cannot be evaluated
        """

        loc = dict()
        if hasattr(environment, "get_data"):
            loc.update(environment.get_data())
        
        glo = dict()
        # We need to have the "__import__" function, because is needed by a lot of things. 
        # Let's try at least to don't allow the user to call it explicitly, probably this check 
		# can be easily passed around...
        builtins = dict(__import__ = __import__)
            
        glo['__builtins__'] = builtins

        try:
            if "__import__" in expr:
                raise ValueError("You cannot use __import__!")
                
            val = eval(expr, glo, loc)
        except AttributeError, err:
            e = err.args[0]
            i = e.find(" attribute ")
            i += len(" attribute ")
            msg = "Invalid variable/function name: %s"%e[i:]
            raise ReportError(msg)
        except StandardError, e:
            raise ReportError(str(e))
            
        return val
    
    def get_system_fonts(self):
        pass
        
class Variable(object):
    """
    This is a report-defined variable.
    """
    
    vartypes={
              'integer': int,
              'string': unicode,
              'decimal': decimal.Decimal,
              'float': float,
              'date': datetime.date
    }
    
    def __init__(self,name,type,value=None):
        """
        Constructor
        @param name: Variable's name
        @param type: Variable's type (one of vartypes strings)
        @param value: Current value, or None
        """
        
        if not type in self.__class__.vartypes:
            raise ReportError("Invalid variable type %s for variable %s"%type,name)
            
        self.name=name
        self.type=type
        try:
            self.value=self.__class__.vartypes[type](value)
        except TypeError:
            self.value=None

class Parameter(Variable):
    """
    A Parameter is a special type of Variable, its initial value is given by the caller.
    """
    pass

class Calculation(object):
    """
    An automatic calculation made on the datasource
    """
    
    def __init__(self, type, variable, value, reset = "end", startvalue = None):
        if not type in ("sum", "avg", "min", "max", "assign"):
            raise ReportError("Invalid calculation type: %s"%type)
        
        if not reset in ("end", "page"):
            raise ReportError("Invalid reset value: %s"%reset)
        
        self.type = type
        
        self.variable = variable
        self.value = value
        self.reset_at = reset
        
        self.startvalue = None
        
        if self.startvalue is not None:
            self.value = self.startvalue
    
        self.partial = 0
        self.count = 0
        
        self.report = None
        
    def reset(self):
        if self.startvalue is not None:
            self.partial = self.startvalue
        else:
            self.partial = None
            
        self.count = 0
        
    def execute(self, renderer, environment):
        self.count += 1
        
        if not self.variable in self.report.variables.values():
            raise ReportError("Variable not found:"%self.variable)
        
        val = renderer.safe_eval(self.value, environment)
        if self.partial is None:
            self.partial = val
            
        if self.type == "sum":
            self.partial += val
            self.variable.value = self.partial
        elif self.type == "avg":
            self.partial += val
            self.variable.value = self.partial/self.count
        elif self.type == "min":
            if val < self.partial:
                self.partial = val
            self.variable.value = self.partial
        elif self.type == "max":
            if val > self.partial:
                self.partial = val
            self.variable.value = self.partial
        elif self.type == "assign":
            self.variable.value = val
