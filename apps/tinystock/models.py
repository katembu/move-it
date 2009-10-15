# coding=utf-8

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from datetime import datetime

from apps.reporters.models import *
from apps.locations.models import *

class KindOfItem(models.Model):
    ''' Primary categorization of an item.
        can be 'Tablet' or 'Dose' in a health context.
        code PK allows sms lookup'''
    code    = models.CharField(max_length=16, primary_key=True)
    name    = models.CharField(max_length=64)

    def __unicode__(self):
        return u"%(n)s (%(c)s)" % {'n': self.name, 'c': self.code}

class Item(models.Model):
    ''' Items to be stored. Think it as Drug'''
    sku     = models.CharField(max_length=64, primary_key=True)
    code    = models.CharField(max_length=16, unique=True)
    kind    = models.ForeignKey('KindOfItem')
    name    = models.CharField(max_length=64)

    def __unicode__(self):
        return self.display_name() #u"<%(sku)s:%(txt)s>" % {'sku': self.sku, 'txt': self.name[:30]}

    def display_name(self):
        return u"%(name)s (%(kind)s#%(code)s)" % {'name': self.name, 'code': self.code, 'kind': self.kind.code}

    @classmethod
    def by_sku (cls, sku):
        try:
            return cls.objects.get(sku=sku)
        except models.ObjectDoesNotExist:
            return None

    @classmethod
    def by_code (cls, code):
        try:
            return cls.objects.get(code=code)
        except models.ObjectDoesNotExist:
            return None

class StockItem(models.Model):
    ''' combination of an Item and a quantity '''

    class Meta:
        unique_together = (("_peer_reporter", "item"),("_peer_location", "item"),)

    _peer_reporter  = models.ForeignKey(Reporter, blank=True, null=True)
    _peer_location  = models.ForeignKey(Location, blank=True, null=True)
    item    = models.ForeignKey('Item')
    quantity= models.IntegerField()

    def __unicode__(self):
        return u"%(peer)s, %(item)s: %(q)s %(kind)s" % {'q': self.quantity, 'kind': self.item.kind.name, 'item': self.item.name, 'peer': self.peer}

    def set_peer(self, value):
        if value.__class__ == Reporter:
            self._peer_reporter   = value
            self._peer_location   = None
        elif value.__class__ == Location:
            self._peer_location   = value
            self._peer_reporer    = None
        else:
            raise ValueError

    def get_peer(self):

        if self._peer_reporter: return self._peer_reporter
        if self._peer_location: return self._peer_location
        return None

    peer = property(get_peer, set_peer)

    @classmethod
    def by_peer(cls, peer):
        
        # reporter
        try:
            stores       = cls.objects.filter(_peer_reporter=peer)
            return stores
        except:
            pass

        # location
        try:
            stores       = cls.objects.filter(_peer_location=peer)
            return stores
        except:
            pass

        raise StockItem.DoesNotExist

    @classmethod
    def by_peer_item(cls, peer, item):
        try:
            filtered    = cls.objects.filter(item=item)
        except:
            raise StockItem.DoesNotExist

        # reporter
        try:
            stock       = filtered.get(_peer_reporter=peer)
            return stock
        except:
            pass

        # location
        try:
            stock       = filtered.get(_peer_location=peer)
            return stock
        except:
            pass

        raise StockItem.DoesNotExist

    @classmethod
    def new_by_peer_item_qty(cls, peer, item, quantity):
        if peer.__class__ == Reporter:
            stock   = StockItem(_peer_reporter=peer, item = item, quantity = quantity)
        elif peer.__class__ == Location:
            stock   = StockItem(_peer_location=peer, item = item, quantity = quantity)
        else:
            raise ValueError

        stock.save()
        return stock
        

class TransferLog(models.Model):

    STATUS_OK           = 1
    STATUS_CANCELLED    = 2
    STATUS_CONFLICT     = 3
    
    STATUS_CHOICES = (
        (STATUS_OK,         _('Processed')),
        (STATUS_CANCELLED,  _('Cancelled')),
        (STATUS_CONFLICT,   _('Conflict')),
    )
    
    date    = models.DateTimeField(auto_now_add=True)
    _sender_reporter    = models.ForeignKey(Reporter, blank=True, null=True, related_name='transfer_sender')
    _sender_location    = models.ForeignKey(Location, blank=True, null=True, related_name='transfer_sender')
    _receiver_reporter    = models.ForeignKey(Reporter, blank=True, null=True, related_name='transfer_receiver')
    _receiver_location    = models.ForeignKey(Location, blank=True, null=True, related_name='transfer_receiver')
    item    = models.ForeignKey('Item')
    quantity= models.IntegerField()
    status  = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_OK)
    note = models.TextField(blank=True)
    
    def __unicode__(self):
        return u"%(d)s: %(s)s>%(r)s - %(q)s %(it)s" % {'s': self.sender, 'r': self.receiver, 'q': self.quantity, 'it': self.item.name, 'd': self.date.strftime("%Y%m%d")}

    def set_sender(self, value):
        if value.__class__ == Reporter:
            self._sender_reporter   = value
            self._sender_location   = None
        elif value.__class__ == Location:
            self._sender_location   = value
            self._sender_reporer    = None
        else:
            raise ValueError

    def get_sender(self):

        if self._sender_reporter: return self._sender_reporter
        if self._sender_location: return self._sender_location
        return None

    sender = property(get_sender, set_sender)

    def set_receiver(self, value):
        if value.__class__ == Reporter:
            self._receiver_reporter   = value
            self._receiver_location   = None
        elif value.__class__ == Location:
            self._receiver_location   = value
            self._receiver_reporer    = None
        else:
            raise ValueError

    def get_receiver(self):

        if self._receiver_reporter: return self._receiver_reporter
        if self._receiver_location: return self._receiver_location
        return None

    receiver = property(get_receiver, set_receiver)

    

