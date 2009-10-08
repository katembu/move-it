#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from datetime import date, datetime

import rapidsms
from rapidsms.parsers.keyworder import * 
from django.utils.translation import ugettext as _

from apps.reporters.models import *
from apps.locations.models import *
from apps.rdtreporting.models import *
from apps.rdtreporting.utils import *
from apps.tinystock.models import KindOfItem, Item, StockItem
from apps.tinystock.logic import *
from apps.tinystock.exceptions import *
from utils import *

class HandlerFailed (Exception):
    pass

class MalformedRequest (Exception):
    pass

class AmbiguousAlias (Exception):
    pass

def registered (func):
    def wrapper (self, message, *args):
        if message.persistant_connection.reporter:
            return func(self, message, *args)
        else:
            message.respond(_(u"Sorry, only registered users can access this program."))
            return True
    return wrapper

def admin (func):
    def wrapper (self, message, *args):
        reporter = message.persistant_connection.reporter
        if reporter and ReporterGroup.objects.get(title='admin') in reporter.groups.only():
            return func(self, message, *args)
        else:
            message.respond(_(u"Sorry, only administrators of the system can perform this action."))
            return False
    return wrapper

def rec_type_from_string(rec_type):
    if rec_type == '@':
        rec_type    = None
    if rec_type == '@@':
        rec_type    = Reporter
    if rec_type == '@@@':
        rec_type    = Location
    return rec_type

def stock_answer(target):


    stores   = StockItem.by_peer(peer=target)
 
    total = stores.extra(select={'total': 'SUM(quantity)'})[0].total
    if total == None:
        total = 0

    if total == 0:
        return _(u"%(user)s has nothing") % {'user': target}
 
    answer  = _(u"%(user)s has: ") % {'user': target}
    sep     = u", "
    stock   = stores
    for couple in stock:
        answer += _(u"%(med)s (#%(sku)s|%(k)s): %(q)s") % {'med': couple.item.name, 'q': couple.quantity, 'k': couple.item.kind.code, 'sku': couple.item.sku}
        answer += sep
    return answer[:-sep.__len__()]

def peer_from_alias(alias, of_type=None):

    try:
        reporter    = Reporter.objects.get(alias=alias)
    except models.ObjectDoesNotExist:
        reporter    = None

    try:
        location    = Location.objects.get(code=alias)
    except models.ObjectDoesNotExist:
        location    = None

    if reporter and location:
        if of_type and of_type.__class__ == django.db.models.base.ModelBase:
            return reporter if of_type == Reporter else location
        elif of_type:
            return reporter, location
        else:
            raise AmbiguousAlias

    return reporter if reporter else location

class App (rapidsms.app.App):

    keyword = Keyworder()

    def start (self):
        pass

    def handle (self, message):
        try:
            func, captures = self.keyword.match(self, message.text)
        except TypeError:
            # didn't find a matching function
            message.respond(_(u"Error. Your message could not be recognized by the system. Please check syntax and retry."))
            return False
        try:
            handled = func(self, message, *captures)
        except HandlerFailed, e:
            print e
            handled = True
        except Exception, e:
            print e
            message.respond(_(u"An error has occured (%(e)s).") % {'e': e})
            raise
        message.was_handled = bool(handled)
        return handled

    ############################
    #  REGISTRATION
    ############################

    # SUBSCRIBE
    keyword.prefix = ["subscribe"]
    @keyword(r'(\w+) (\w+) (.+)')
    def join(self, message, clinic_code, role_code, name):
        ''' register a user and join the system '''

        try:
            # parse the name, and create a reporter
            alias, fn, ln = Reporter.parse_name(name)
            rep = Reporter(alias=alias, first_name=fn, last_name=ln)
            rep.save()
            
            # attach the reporter to the current connection
            message.persistant_connection.reporter = rep
            message.persistant_connection.save()
                  
            # something went wrong - at the
            # moment, we don't care what
        except:
            message.respond("Join Error. Unable to register your account.")

        if role_code == None or role_code.__len__() < 1:
            role_code   = 'hw'

        reporter    = message.persistant_connection.reporter

        return self.join_reporter(message, reporter, clinic_code, role_code)

    # JOIN
    keyword.prefix = ["join"]
    @keyword(r'(\w+)\s?(\w*)')
    @registered
    def join(self, message, clinic_code, role_code):
        ''' Adds a self-registered reporter to the mrdt system '''

        if role_code == None or role_code.__len__() < 1:
            role_code   = 'hw'

        reporter    = message.persistant_connection.reporter

        return self.join_reporter(message, reporter, clinic_code, role_code)

    # JOIN (ADMIN)
    keyword.prefix = ["subscribe", "join"]
    @keyword(r'\@(slug) (letters)\s?(\w*)')
    @registered
    @admin
    def join_one(self, message, reporter_alias, clinic_code, role_code):
        ''' Adds an arbitrary reporter to the mrdt system '''

        if role_code == None or role_code.__len__() < 1:
            role_code   = 'hw'

        try:
            reporter    = Reporter.objects.get(alias=reporter_alias)
        except models.ObjectDoesNotExist:
            message.respond(_("Join Error. The provided alias (%(alias)s) does not exist in the system") % {'alias': reporter_alias})
            return True

        return self.join_reporter(message, reporter, clinic_code, role_code)
        
    def join_reporter(self, message, reporter, clinic_code, role_code):
        ''' sets a location and role for a reporter and mark him active '''

        # check clinic code
        try:
            clinic  = Location.objects.get(code=clinic_code)
        except models.ObjectDoesNotExist:
            message.forward(reporter.connection().identity, \
                _(u"Join Error. Provided Clinic code (%(clinic)s) is wrong.") % {'clinic': clinic_code})
            return True
    
        # check that location is a clinic (not sure about that)
        if not clinic.type in LocationType.objects.filter(name__startswith='HC'):
            message.forward(reporter.connection().identity, \
                _(u"Join Error. You must provide a Clinic code."))
            return True

        # set location
        reporter.location = clinic

        # check role code
        try:
            role  = Role.objects.get(code=role_code)
        except models.ObjectDoesNotExist:
            message.forward(reporter.connection().identity, \
                _(u"Join Error. Provided Role code (%(role)s) is wrong.") % {'role': role_code})
            return True

        reporter.role   = role

        # set account active
        # /!\ we use registered_self as active
        reporter.registered_self  = True

        # save modifications
        reporter.save()

        # inform target
        message.forward(reporter.connection().identity, \
            _("Success. You are now registered as %(role)s at %(clinic)s with alias @%(alias)s.") % {'clinic': clinic, 'role': reporter.role, 'alias': reporter.alias})

        #inform admin
        if message.persistant_connection.reporter != reporter:
            message.respond( \
            _("Success. %(reporter)s is now registered as %(role)s at %(clinic)s with alias @%(alias)s.") % {'reporter': reporter, 'clinic': clinic, 'role': reporter.role, 'alias': reporter.alias})
        return True

    # STOP
    keyword.prefix = ["stop", "pause"]
    @keyword.blank()
    @registered
    def stop(self, message):
        ''' Disables the sender in the system '''

        reporter    = message.persistant_connection.reporter

        return self.stop_reporter(message, reporter)

    # STOP (ADMIN)
    keyword.prefix = ["stop", "pause"]
    @keyword(r'\@(slug)')
    @registered
    @admin
    def stop_one(self, message, reporter_alias):
        ''' Disables an arbitrary reporter in the system '''

        try:
            reporter    = Reporter.objects.get(alias=reporter_alias)
        except models.ObjectDoesNotExist:
            message.respond(_("Stop Error. The provided alias (%(alias)s) does not exist in the system") % {'alias': reporter_alias})
            return True

        return self.stop_reporter(message, reporter)

    def stop_reporter(self, message, reporter):
        ''' mark a reporter innactive in the system '''

        if not reporter.registered_self:
            message.respond(_("%(reporter)s is already inactive.") % {'reporter': reporter})
            return True

        # set account inactive
        # /!\ we use registered_self as active
        reporter.registered_self  = False

        # save modifications
        reporter.save()

        # inform target
        message.forward(reporter.connection().identity, \
            _("Success. You are now out of the system. Come back by sending BACK."))

        #inform admin
        if message.persistant_connection.reporter != reporter:
            message.respond( \
            _("Success. %(reporter)s is now out of the system.") % {'reporter': reporter})
        return True

    # BACK
    keyword.prefix = ["back", "resume"]
    @keyword.blank()
    @registered
    def back(self, message):
        ''' Enables again the sender in the system '''

        reporter    = message.persistant_connection.reporter

        return self.back_reporter(message, reporter)

    # BACK (ADMIN)
    keyword.prefix = ["back", "resume"]
    @keyword(r'\@(slug)')
    @registered
    @admin
    def back_one(self, message, reporter_alias):
        ''' Enables again an arbitrary reporter in the system '''

        try:
            reporter    = Reporter.objects.get(alias=reporter_alias)
        except models.ObjectDoesNotExist:
            message.respond(_("Stop Error. The provided alias (%(alias)s) does not exist in the system") % {'alias': reporter_alias})
            return True

        return self.back_reporter(message, reporter)

    def back_reporter(self, message, reporter):
        ''' mark a reporter active in the system '''

        if reporter.registered_self:
            message.respond(_("%(reporter)s is already active.") % {'reporter': reporter})
            return True

        # set account inactive
        # /!\ we use registered_self as active
        reporter.registered_self  = True

        # save modifications
        reporter.save()

        # inform target
        message.forward(reporter.connection().identity, \
            _("Success. You are back in the system with alias %(alias)s.") % {'alias': reporter.alias})

        #inform admin
        if message.persistant_connection.reporter != reporter:
            message.respond( \
            _("Success. %(reporter)s is back as %(role)s at %(clinic)s.") % {'reporter': reporter, 'clinic': reporter.location, 'role': reporter.role})
        return True

    # LOOKUP
    keyword.prefix = ["lookup", "search"]
    @keyword(r'(letters)\s?(\w*)')
    @registered
    def back(self, message, clinic_code, name):
        ''' List reporters from a location matching a name '''

        # check clinic code
        try:
            clinic  = Location.objects.get(code=clinic_code)
        except models.ObjectDoesNotExist:
            message.forward(reporter.connection().identity, \
                _(u"Lookup Error. Provided Clinic code (%(clinic)s) is wrong.") % {'clinic': clinic_code})
            return True

        # get list of reporters
        reporters   = Reporter.objects.filter(location=clinic, registered_self=True)
        print reporters
        if name != None and name.__len__() > 0:
            print name
            reporters   = reporters.filter(first_name__contains=name)
            print reporters

        if reporters.__len__() == 0:
            message.respond(_("No such people at %(clinic)s.") % {'clinic': clinic})
            return True           
        
        msg     = ""
        msg_stub= _(u"%(reporter)s/%(alias)s is %(role)s at %(clinic)s with %(number)s")

        # construct answer
        for areporter in reporters:
            mst     = msg_stub % {'reporter': areporter, 'alias': areporter.alias, 'role': areporter.role.code.upper(), 'clinic': areporter.location.code.upper(), 'number': areporter.connection().identity}
            if msg.__len__() == 0:
                msg = mst
            else:
                msg = _(u"%s, %s") % (msg, mst)

        # strip long list
        if msg.__len__() >= 160:
            intro   = _("%(nb)s results. ") % {'nb': reporters.__len__()}
            msg     = intro + msg[:-intro.__len__()]

        # answer
        message.respond(msg)
        
        return True

    ############################
    #  RDT REPORTING
    ############################

    # REGISTERING MRDT
    keyword.prefix = ["rdt", "mrdt"]
    @keyword(r'([0-9]{6}) (numbers) (numbers) (numbers) (numbers)')
    @registered
    def back(self, message, date, tested, confirmed, treatments, used):
        ''' List reporters from a location matching a name '''

        reporter    = message.persistant_connection.reporter
        
        try:
            report, overwritten = record_mrdt(reporter, int(tested), int(confirmed), int(treatments), int(used), day=date, overwrite=True)
        except UnknownReporter:
            message.respond(_(u"Report Failed. You are not allowed to report MRDT."))
            return True
        except DuplicateReport:
            message.respond(_(u"Report Failed. Your datas for %(date)s have already been reported.") % {'date': date})
            return True
        except ErroneousDate:
            message.respond(_(u"Report Failed. Provided date (%(date)s) is erroneous.") % {'date': date})
            return True
        except IncoherentValue:
            message.respond(_(u"Report Failed. Provided values are incoherent."))
            return True

        if overwritten:
            suffix  = _(u" (overwrite)")
        else:
            suffix  = ""

        message.respond(_("Clinic #%(clinic_id)s %(clinic)s %(date)s report received%(overwrite_suffix)s! Cases=%(tested)s, Positive=%(confirmed)s Treatment=%(treatments)s, Tests=%(used)s") % {'clinic_id': report.reporter.location.id, 'clinic': report.reporter.location, 'date': report.date.strftime("%d.%m.%Y"), 'overwrite_suffix': suffix, 'tested': report.tested, 'confirmed': report.confirmed, 'treatments': report.treatments, 'used': report.used})

        return True

    ############################
    #  DRUG TRANSFERS
    ############################

    def do_transfer_drug(self, message, sender, receiver, item, quantity):
        
        log = transfer_item(sender=sender, receiver=receiver, item=item, quantity=int(quantity))
       
        if receiver.connection():
            message.forward(receiver.connection().identity, "CONFIRMATION #%(d)s-%(sid)s-%(rid)s-%(lid)s You have received %(quantity)s %(item)s from %(sender)s. If not correct please reply: CANCEL %(lid)s" % {
                'quantity': quantity,
                'item': item.name,
                'sender': sender,
                'd': log.date.strftime("%d%m%y"),
                'sid': sender.id,
                'rid': receiver.id,
                'lid': log.id
            })

        message.respond("CONFIRMATION #%(d)s-%(sid)s-%(rid)s-%(lid)s You have sent %(quantity)s %(item)s to %(receiver)s. If not correct please reply: CANCEL %(lid)s" % {
            'quantity': quantity,
            'item': item.name,
            'receiver': receiver,
            'd': log.date.strftime("%d%m%y"),
            'sid': sender.id,
            'rid': receiver.id,
            'lid': log.id
        })

        # remove stock alert if applicable

        if not receiver.__class__ == Reporter:
            return True

        alerts  = RDTStockAlert.objects.filter(reporter=receiver, status=RDTStockAlert.STATUS_SENT)
        if not alerts.count() > 0:
            return True

        # get low level
        try:
            low = Configuration.objects.get(id=1).low_stock_level
        except:
            return True

        mrdt    = Item.by_code('mrdt')
        stock  = StockItem.by_peer_item(peer=receiver, item=mrdt)

        if stock.quantity >= low:
            for alert in list(alerts):
                alert.status    = RDTStockAlert.STATUS_FIXED
                alert.save()
        else:
            for alert in list(alerts):
                alert.status    = RDTStockAlert.STATUS_OBSOLETE
                alert.save()

        return True

    # DIST
    keyword.prefix = ['dist']
    @keyword(r'(@|@@|@@@)(\w+) (\d+)')
    @registered
    def transfer_clinic_chw (self, message, rec_type, receiver, quantity):
        ''' Transfer Drug from Reorter to Clinic or Reporter
            DIST @mdiallo #001 10'''

        # Assume we only have MRDT
        code    = 'mrdt'

        rec_type    = rec_type_from_string(rec_type)
        
        alias=receiver.lower()

        # sender is the one emiting the text
        sender      = message.persistant_connection.reporter
        try:
            receiver    = peer_from_alias(alias)
        # There is a location AND a reporter with same alias
        except AmbiguousAlias:
            # User may not know that he can enforce a recipient
            if rec_type == None:
                message.respond(_(u"Distribution request failed. Alias is ambiguous. Use @@ to enforce a Reporter of @@@ to enforce Clinic/Location alias."))
                return True
            else:
                receiver= peer_from_alias(alias, of_type=rec_type)

        item        = Item.by_code(code)
        if item == None or sender == None or receiver == None:
            message.respond(_(u"Distribution request failed. Either Item ID or CHW alias is wrong."))
            return True

        try:
            return self.do_transfer_drug(message, sender, receiver, item, quantity)
        except ItemNotInStore:
            message.respond(_(u"Distribution request failed. You do not have %(med)s") % {'med': item})
            return True
        except NotEnoughItemInStock:
            message.respond(_(u"Distribution request failed. You can't transfer %(q)s %(it)s to %(rec)s because you only have %(stk)s.") % {'q': quantity, 'it': item.name, 'rec': receiver, 'stk': StockItem.by_peer_item(peer=sender, item=item).quantity})
            return True

    # ADD (admin)
    keyword.prefix  = ['add']
    @keyword(r'(\d+)')
    @registered
    @admin
    def add_stock (self, message, quantity):
        
        ''' Add stock for item. Used by main drug distribution point'''

        # Assume we only have MRDT
        code    = 'mrdt'

        sender      = message.persistant_connection.reporter
        
        # only PHA can add drugs
        try:
            no_pha  = not sender.role == Role.objects.get(code='pha')
        except:
            no_pha  = True        

        if no_pha:
            message.respond(_(u"Addition request failed. Only PHA can perform such action."))
            return True

        receiver    = sender
        item        = Item.by_code(code)
        if item == None or sender == None or receiver == None:
            message.respond(_(u"Addition request failed. Either Item ID or Reporter alias is wrong."))
            return True
        
        try:
            log = add_stock_for_item(receiver=receiver, item=item, quantity=int(quantity))
        
            message.respond("CONFIRMATION #%(d)s-%(sid)s-%(lid)s You have added %(quantity)s %(item)s to your stock. If not correct please reply: CANCEL %(lid)s" % {
            'quantity': quantity,
            'item': item.name,
            'receiver': receiver,
            'd': log.date.strftime("%d%m%y"),
            'sid': sender.id,
            'rid': receiver.id,
            'lid': log.id
            })
        except:
            raise

        return True

    def parse_sku_quantities(self, sku_quantities):
        ''' returns array of hash from SKU quantities format '''

        couples  = sku_quantities.split(" #")
        skq = {}
        try:
            for couple in couples:
                x = couple.split(" ")
                code = x[0].replace("#", "")
                item = Item.by_code(code)
                if skq.has_key(code) or item == None:
                    raise MalformedRequest
                skq[code]   = {'code': code, 'quantity': int(x[1]), 'item': item}
            return skq
        except IndexError:
            raise MalformedRequest

    # CDIST (disabled)
    keyword.prefix  = ['cdist']
    @keyword(r'(@|@@|@@@)(\w+)(.+)')
    @registered
    def bulk_transfer_clinic_chw (self, message, rec_type, receiver, sku_quantities):
        ''' Transfer Multiple Drugs from Clinic to CHW
            CDIST @mdiallo #001 10 #004 45 #007 32'''

        # Disable CDIST for now since we only have MRDT
        return False

        sender      = message.persistant_connection.reporter

        # let's find receiver        
        rec_type    = rec_type_from_string(rec_type)
        alias       = receiver.lower()
        try:
            receiver    = peer_from_alias(alias)
        # There is a location AND a reporter with same alias
        except AmbiguousAlias:
            # User may not know that he can enforce a recipient
            if rec_type == None:
                message.respond(_(u"Distribution request failed. Alias is ambiguous. Use @@ to enforce a Reporter of @@@ to enforce Clinic/Location alias."))
                return True
            else:
                receiver= peer_from_alias(alias, of_type=rec_type)

        if sku_quantities == None or sender == None or receiver == None:
            message.respond(_(u"Distribution request failed. Either Item IDs or CHW alias is wrong."))
            return True

        try:
            sq  = self.parse_sku_quantities(sku_quantities)
        except MalformedRequest:
            message.respond(_(u"Distribution failed. Syntax error in drugs/quantities statement."))
            return True
        
        success = []
        failures= []
        for code in sq.itervalues():
            try:
                self.do_transfer_drug(message, sender, receiver, code['item'], code['quantity'])
                success.append(code)
            except (NotEnoughItemInStock, ItemNotInStore, Exception):
                failures.append(code)
                continue
        
        if failures.__len__() == 0:
            message.respond(_(u"SUMMARY: Multiple Drugs Distribution went through successfuly."))
            return True
        
        if success.__len__() == 0:
            message.respond(_(u"SUMMARY: complete FAILURE. Multiple Drugs Distribution went wrong on all items."))
            return True

        # some failed, some went trough
        details = u""
        for fail in failures:
            details += u"%s, " % fail['item'].name
        details = details[:-2]
        message.respond(_(u"SUMMARY: Some items couldn't be transfered: %(detail)s") % {'detail': details})
        return True      

    def stock_for(self, message, provider):
        ''' returns list of drugs + quantities for a provider '''

        if provider == None:
            return False
        msg = stock_answer(provider)
        message.respond(msg)
        return msg

    # STOCK @
    keyword.prefix  = ['stock']
    @keyword(r'(@|@@|@@@)(\w+)')
    @registered
    def request_stock (self, message, rec_type, target):
        ''' Get stock status for someone.
            /!\ limited to providers ; no locations or others
            STOCK @mdiallo'''

        # let's find receiver        
        rec_type    = rec_type_from_string(rec_type)     
        alias       = target.lower()
        try:
            receiver    = peer_from_alias(alias)
        # There is a location AND a reporter with same alias
        except AmbiguousAlias:
            # User may not know that he can enforce a recipient
            if rec_type == None:
                message.respond(_(u"Stock request failed. Alias is ambiguous. Use @@ to enforce a Reporter of @@@ to enforce Clinic/Location alias."))
                return True
            else:
                receiver= peer_from_alias(alias, of_type=rec_type)
        
        return self.stock_for(message, receiver)

    # STOCK
    keyword.prefix  = ['stock']
    @keyword.blank()
    @registered
    def request_self_stock (self, message):
        ''' Get stock status for a store
            STOCK'''
        
        provider    = message.persistant_connection.reporter
        return self.stock_for(message, provider)

    # CANCEL
    keyword.prefix  = ['cancel']
    @keyword(r'(\d+)')
    @registered
    def cancel_request (self, message, cancel_id):
        ''' Cancel a transfer request
            CANCEL 908432'''
        
        # retrieve transaction
        try:
            log = TransferLog.objects.get(id=int(cancel_id))
        except TransferLog.DoesNotExist:
            message.respond(_(u"Cancellation failed. Provided transaction ID (%(lid)s) is wrong.") % {'lid': cancel_id})
            return True

        # Check request is legitimate
        try:
            peer    = message.persistant_connection.reporter
        except:
            peer    = None
        if peer == None or (log.sender, log.receiver).count(peer) == 0:
            message.respond(_("Cancellation failed. With all due respect, you are not allowed to perform this action."))
            return True

        # Check is transfer hasn't already been cancelled
        if (TransferLog.STATUS_CANCELLED, TransferLog.STATUS_CONFLICT).count(log.status) != 0 :
            message.respond(_("Cancellation failed. Transfer #%(lid)s dated %(date)s has already been canceled or is in conflict.") % {'lid': log.id, 'date': log.date.strftime("%b %d %y %H:%M")})
            return True
        
        # cancellation attempt
        other_peer  = log.receiver if peer == log.sender else log.sender

        # if peer is a patient, don't send messages
        try:
            peer_is_patient = not other_peer.connection()
        except:
            peer_is_patient = True

        try:
            cancel_transfer(log)
            msg = _(u"CANCELLED Transfer #%(lid)s dated %(date)s by request of %(peer)s. Please forward conflict to Drug Store Head.") % {'lid': log.id, 'date': log.date.strftime("%b %d %y %H:%M"), 'peer': peer}
            message.respond(msg)
            if not peer_is_patient:
                message.forward(other_peer.connection().identity, msg)
        except (ItemNotInStore, NotEnoughItemInStock):
            # goods has been transfered elsewhere.
            msg = _(u"Cancellation failed. %(peer)s has started distributing drugs from transaction #%(lid)s. Contact Drug Store Head.") % {'lid': log.id, 'peer': log.receiver}
            message.respond(msg)
            if not peer_is_patient:
                message.forward(other_peer.connection().identity, msg)
        except Provider.DoesNotExist:
            pass
        return True

    # UPDATE
    keyword.prefix = ['update']
    @keyword(r'(\d+)')
    @registered
    def update_quantity (self, message, quantity):
        ''' Update quantities of drug and transfer to Lost accordingly '''

        # Assume we only have MRDT
        code    = 'mrdt'

        # sender is the one emiting the text
        sender  = message.persistant_connection.reporter
        receiver= get_lostItems()

        item        = Item.by_code(code)
        if item == None or sender == None or receiver == None:
            message.respond(_(u"Update failed. Either Item ID or CHW alias is wrong."))
            return True

        # grab stored quantity and provided
        stock_qty   = StockItem.by_peer_item(sender, item).quantity
        quantity= int(quantity)
        
        # compare stored and update
        if stock_qty > quantity:
            # Transfer difference to Lost
            diff= stock_qty - quantity
            log = transfer_item(sender=sender, receiver=receiver, item=item, quantity=diff)
            message.respond(_(u"Update recorded. You have lost %(nblost)s MRDTs since last update.") % {'nblost': diff})
            return True
        elif quantity > stock_qty:
            # Should not happen. Warn user
            diff= quantity - stock_qty
            message.respond(_(u"Update failed. You appear to have %(nbextra)s more MRDTs than expected. Please contact Drug Store Head ASAP.") % {'nbextra': diff})
            return True
        else:
            # Well done pal!
            message.respond(_(u"Update recorded. Congratulations, you did a great job managing your MRDTs"))
            return True

