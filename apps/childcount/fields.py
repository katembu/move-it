from django.utils.translation import ugettext as _
from django.forms.fields import CharField
from django.forms import ModelForm
from django import forms
from django.forms import TextInput
from django.forms.util import ValidationError

from childcount.widgets import JQueryAutoComplete
from childcount.models.Patient import Patient

class HealthIdField(CharField):
    def __init__(self, *args, **kwargs):
        super(HealthIdField, self).__init__(*args, **kwargs)
        if self.initial != None:
            self.initial = Patient\
                .objects\
                .get(pk=self.initial)\

    def clean(self, value):
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
    class Meta:
        model = Patient
        exclude = ['health_id']

    def __init__(self, *args, **kwargs):
        super(PatientForm, self).__init__(*args, **kwargs)
        patients = Patient.objects.filter(location=self.instance.location)
        # potential HoHH are HoHH from same village
        self.fields['household'].choices = [(p.id, p.__unicode__()) \
                                 for p in patients if p.is_head_of_household()]
        # potential mothers are female aged 13+ from same village
        self.fields['mother'].choices = [('','---------')] + \
                                        [(p.id, p.__unicode__()) for p in \
              patients.filter(gender=Patient.GENDER_FEMALE) if p.years() >= 13]
