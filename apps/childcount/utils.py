from functools import wraps
from django.utils.translation import gettext as _

from childcount.exceptions import NotRegistered

def authenticated(func):
    ''' decorator checking if sender is allowed to process feature.

    checks if sender property is set on message

    return function or boolean '''

    @wraps(func)
    def wrapper(self, *args):
        if self.message.persistant_connection.reporter:
            return func(self, *args)
        else:
            raise NotRegistered(_("%(number)s is not a registered number.")
                            % {'number': self.message.peer})
            return False
    return wrapper