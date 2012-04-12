
#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

"""Useful form fields and widgets for
dealing with health IDs.
"""

from django.conf import settings
from django.utils.translation import ugettext as _
from django.forms.fields import CharField
from django.forms import ModelForm
from django import forms
from django.forms import TextInput
from django.forms.util import ValidationError

from django.contrib.auth.models import Group
from childcount.models import Patient, CHW
from locations.models import Location

class HealthIdWidget(forms.TextInput):
    """Defines a widget for health IDs
    that looks like normal text input box but
    displays health IDs nicely.
    """

    def _format_value(self, value):
        if value is None:
            return ''
        
        if isinstance(value, (int, long)):
            return Patient.objects.get(pk=value).health_id.upper()
        return value.upper()

    def _has_changed(self, initial, data):
        return super(HealthIdWidget, self).has_changed(self._format_value(initial), data)

    def render(self, name, value, attrs=None):
        value = self._format_value(value)
        return super(HealthIdWidget, self).render(name, value, attrs)

class HealthIdField(forms.Field):
    """A form field for health IDs
    that does validation of an inputted
    health ID against the existing IDs
    in the database.
    """

    widget = HealthIdWidget

    def clean(self, value):
        super(HealthIdField, self).clean(value)

        value = super(HealthIdField, self).clean(value).upper()
        value = value.strip()

        if value == '': return None
        try:
            p = Patient.objects.get(health_id=value)
        except Patient.DoesNotExist:
            raise ValidationError(_("There is no patient with \
                health ID %(hid)s") % {'hid': value})
        return p

class PatientForm(ModelForm):
    """A Django form for editing :class:`childcount.models.Patient`
    objects.
    Uses the custom health ID input fields.
    """


    class Meta:
        model = Patient
        exclude = ['health_id']

    def __init__(self, *args, **kwargs):
        super(PatientForm, self).__init__(*args, **kwargs)
        patients = Patient.objects.filter(location=self.instance.location)

'''
class CHWForm(ModelForm):
    """A Django form for editing :class:`childcount.models.CHW`
    objects.
    """

    class Meta:
        model = CHW
        exclude = ['is_active', 'username', 'last_login', 'user_permissions', \
                    'date_joined']

'''
class CHWForm(forms.Form):
    #A Django form for editing :class:`childcount.models.CHW`
    #objects.
    
    #username = forms.CharField(max_length=30)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    user_role = forms.ChoiceField(choices=[(group.id, group.name) \
                                       for group in Group.objects.all()])
    location = forms.ChoiceField(choices=[(location.id, location.name) \
                                       for location in Location.objects.all()])

    mchoices = [(chw.id, chw.full_name()) \
                                       for chw in CHW.objects.all()]
    mchoices.append(('','Select Manager'))
    manager = forms.ChoiceField(choices=mchoices, required=False)

    mobile = forms.CharField(required=False)

    #Assigned Location
    assigned = forms.MultipleChoiceField(choices=[(location.id,  \
                                         location.name) \
                                         for location in \
                                            Location.objects.all()], \
                                        label = "Assigned Location ")

