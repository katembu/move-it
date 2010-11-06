from django.utils.translation import ugettext as _
from django.forms.fields import CharField
from django.forms import ModelForm
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

    '''
    household = HealthIdField(\
        max_length=6, \
        widget=JQueryAutoComplete('/childcount/patients/autocomplete/'))
    mother = HealthIdField(\
        max_length=6, \
        widget=JQueryAutoComplete('/childcount/patients/autocomplete/'), \
        required=False)
    '''
    

