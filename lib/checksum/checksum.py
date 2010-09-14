import random

BASE_CHARACTERS = u'0123456789acdefghjklmnprtuvwxy'


class CheckDigitException(Exception):
    def __unicode__(self):
        return repr(self.args[0])

def clean_chars(chars):
    return unicode(chars.lower().strip())

def get_check_digit(identifier, base_chars):
    if len(identifier) == 0:
        raise CheckDigitException('Zero length identifier')

    mod = len(base_chars)
    factor = 1
    sum = 0
    for char in identifier:
        code_point = base_chars.find(char)
        if code_point == -1:
            raise CheckDigitException('Invalid character in identifier')

        addend = factor * code_point
        # Alternate the factor for next loop
        factor = 1 if factor == 2 else 2

        addend = (addend / mod) + (addend % mod)
        sum += addend
    remainder = sum % mod
    check_code_point = mod - remainder
    check_code_point %= mod
    return base_chars[check_code_point]

def is_valid_identifier(identifier, base_chars = BASE_CHARACTERS):
    try:
        identifier = clean_chars(identifier)
        base_chars = clean_chars(base_chars)
    except Exception:
        raise CheckDigitException
    if len(identifier) < 2:
        return False
    check_digit = clean_chars(identifier[-1])
    identifier = identifier[:-1]

    try:
        return get_check_digit(identifier, base_chars) == check_digit
    except CheckDigitException:
        return False

