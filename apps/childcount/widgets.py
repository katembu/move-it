
from django import forms
from django.forms.widgets import flatatt
#~ from django.forms.util import smart_unicode
from django.utils.html import escape
from django.utils.simplejson import JSONEncoder

from childcount.models import Patient

class JQueryAutoComplete(forms.TextInput):
    def __init__(self, source, options={}, attrs={}):
        """source can be a list containing the autocomplete values or a
        string containing the url used for the XHR request.
        
        For available options see the autocomplete sample page::
        http://jquery.bassistance.de/autocomplete/"""
        
        self.options = None
        self.attrs = {'autocomplete': 'off', 'size': 50}
        self.source = source
        if len(options) > 0:
            self.options = JSONEncoder().encode(options)
        
        self.attrs.update(attrs)
    
    def render_js(self, field_id):
        if isinstance(self.source, list):
            source = JSONEncoder().encode(self.source)
        elif isinstance(self.source, str):
            source = "'%s'" % escape(self.source)
        else:
            raise ValueError('source type is not valid')
        
        options = ''
        if self.options:
            options += ',%s' % self.options

        return u'$(\'#%s\').autocomplete(%s%s);' % (field_id, source, options)

    def render(self, name, value=None, attrs=None):
        final_attrs = self.build_attrs(attrs, name=name)
        if value:
            print value
            try: 
                p = Patient.objects.get(pk=value)
            except Patient.DoesNotExist:
                try:
                    p = Patient.objects.get(health_id=value)
                except Patient.DoesNotExist:
                    raise
                
            final_attrs['value'] = escape(smart_unicode(p.health_id.upper()))

        if not self.attrs.has_key('id'):
            final_attrs['id'] = 'id_%s' % name    
        
        return u'''<input type="text" %(attrs)s/>
        <script type="text/javascript"><!--//
        %(js)s//--></script>
        ''' % {
            'attrs' : flatatt(final_attrs),
            'js' : self.render_js(final_attrs['id']),
        }

