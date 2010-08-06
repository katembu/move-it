#!/usr/bin/env python
# -*- coding= UTF-8 -*-

import random
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError

from logger.models import IncomingMessage, OutgoingMessage
from logger_ng.models import LoggedMessage
from reporters.models import PersistantConnection


def create_from_logger_msg(msg):
    try:
        reporter = PersistantConnection \
                            .objects.get(backend__slug=msg.backend,
                                         identity=msg.identity).reporter
    except PersistantConnection.DoesNotExist:
        reporter = None
    msg_lng = LoggedMessage(identity=msg.identity, backend=msg.backend,
                            text=msg.text, reporter=reporter)
    msg_lng.save()
    msg_lng.date = msg.date
    msg_lng.save()
    return msg_lng


class Command(BaseCommand):


    def handle(self, *args, **options):
        OUTGOING = LoggedMessage.DIRECTION_OUTGOING
        INCOMING = LoggedMessage.DIRECTION_INCOMING

        # First let's do a sanity check to see if we've already imported
        for i in range(0,5):
            incoming = random.choice(IncomingMessage.objects.all())
            outgoing = random.choice(OutgoingMessage.objects.all())
            try:
                LoggedMessage.objects.get(identity=incoming.identity,
                                          backend=incoming.backend,
                                          text=incoming.text,
                                          date=incoming.date,
                                          direction=INCOMING)
                LoggedMessage.objects.get(identity=outgoing.identity,
                                          backend=outgoing.backend,
                                          text=outgoing.text,
                                          date=outgoing.date,
                                          direction=OUTGOING)
            except LoggedMessage.DoesNotExist:
                continue
            else:
                raise CommandError(u"It appears that you have already " \
                                   u"imported your messages.")

        print u"Importing %d incoming messages..." % \
              IncomingMessage.objects.count()
        for msg in IncomingMessage.objects.all():
            msg_lng = create_from_logger_msg(msg)
            msg_lng.direction = INCOMING
            msg_lng.save()

        print u"Importing %d outgoing messages..." % \
              OutgoingMessage.objects.count()
        count = 0
        for msg in OutgoingMessage.objects.all():
            msg_lng = create_from_logger_msg(msg)
            msg_lng.direction = OUTGOING
            SECONDS = 2
            just_before = msg.date - timedelta(seconds=SECONDS) 
            try:
                orig = LoggedMessage.incoming.get(identity=msg.identity,
                                                  backend=msg.backend,
                                                  date__gte=just_before,
                                                  date__lte=msg.date)
            except (LoggedMessage.DoesNotExist,
                    LoggedMessage.MultipleObjectsReturned):
                pass
            else:
                count += 1
                msg_lng.response_to = orig
            msg_lng.save()
        print u"%d outgoing messages successfully paired with their " \
              u"incoming messages." % count

        print "Importing complete"
