#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

from django.utils.translation import ugettext as _
import rapidsms


class App (rapidsms.app.App):

    def configure(self, title='ChildCount Data Entr', tab_link='/childcount-entry', ):
        pass

    def handle(self, message):
        pass
