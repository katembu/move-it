# coding=utf-8

from django.db import models
from django.contrib.auth.models import User
from apps.tinystock.models import StoreProvider, KindOfItem, Item, StockItem
from django.utils.translation import ugettext_lazy as _
from datetime import datetime

from apps.reporters.models import Reporter, Role
from apps.locations.models import Location

class Facility(Location, StoreProvider):

    def __unicode__ (self): 
        return self.name
        
    class Meta:
        verbose_name_plural = "Facilities"
        app_label = "drugtrack"

class Provider(Reporter, StoreProvider):

    class Meta:
        app_label = "drugtrack"

    def display_name(self):
        if self.first_name or self.last_name:
            return "%s %s" % (self.first_name, self.last_name)
        if self.alias:
            return self.alias
        if self.connection():
            return self.connection().identity
        else:
            return str(self.id)

    def display_full(self):
        if not self.location or self.role != Role.objects.get(code='pha'):
            return self.display_name()
        return _(u"%(n)s at %(p)s") % {'n': self.display_name(), 'p': self.location.name}

    def __unicode__(self):
        return self.display_name()

StoreProvider.set_class(Provider, 'provider')

class Patient(StoreProvider):

    class Meta:
        app_label = "drugtrack"
    
    SEXE_MALE    = 1
    SEXE_FEMALE = 2
    
    SEXE_CHOICES = (
        (SEXE_MALE,    _('Male')),
        (SEXE_FEMALE,  _('Female')),
    )
    
    first_name  = models.CharField(max_length=32, null=True, blank=True)
    last_name   = models.CharField(max_length=32, null=True, blank=True)
    sexe        = models.IntegerField(choices=SEXE_CHOICES, default=SEXE_MALE)
    created_at  = models.DateTimeField(auto_now_add=True)
    age         = models.IntegerField()
    
    def display_name(self):
        if self.first_name or self.last_name:
            return "%s %s" % (self.first_name, self.last_name)
        else:
            return str(self.id)

    def display_full(self):
        return self.display_name()

    def __unicode__(self):
        return self.display_name()

    def display_age(self):
        if self.age < 12:
            return _(u"%(age)sm") % {'age': self.age}
        else:
            return _(u"%(age)sy") % {'age': self.age}

    @classmethod
    def age_from_str (cls, stra):
        age = 0
        try:
            if stra[-1] == 'y':
                age = int(stra[:-1]) * 12
            elif stra[-1] == 'm':
                age = int(stra[:-1])
            else:
                age = int(stra) * 12
        except:
            age = 0
        return age

#StoreProvider.set_class(Patient, 'patient')
