#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

''' Bonjour date helpers '''
import pytz
import datetime 

from babel import Locale
import babel.dates

from bonjour.ethiopian_date import EthiopianDateConverter

from django.conf import settings

TIGRINYA_MONTHS_ABBREVIATED = {
   1 : "EthMon1",
   2 : "EthMon2",
   3 : "EthMon3",
   4 : "EthMon4",
   5 : "EthMon5",
   6 : "EthMon6",
   7 : "EthMon7",
   8 : "EthMon8",
   9 : "EthMon9",
   10 : "EthMon10",
   11 : "EthMon11",
   12 : "EthMon12",
   13 : "EthMon13",
}

TIGRINYA_MONTHS_WIDE = {
   1 : "EthiopianMonth1",
   2 : "EthiopianMonth2",
   3 : "EthiopianMonth3",
   4 : "EthiopianMonth4",
   5 : "EthiopianMonth5",
   6 : "EthiopianMonth6",
   7 : "EthiopianMonth7",
   8 : "EthiopianMonth8",
   9 : "EthiopianMonth9",
   10 : "EthiopianMonth10",
   11 : "EthiopianMonth11",
   12 : "EthiopianMonth12",
   13 : "EthiopianMonth13",
}

def _format_date_ethiopian(date, format):
    locale = Locale.parse('ti_ET')
    
    if date is None:
        date = datetime.date.today()

    # Day of week with Monday=0
    dow = date.isoweekday() - 1

    # Convert date to Julian calendar
    (jyear, jmonth, jday) = EthiopianDateConverter.date_to_ethiopian(date)
   
    # Uses the babel.dates codes for substitutions
    sub_dict = {
        'EEEE': locale.days['format']['wide'][dow],
        'EEE': locale.days['format']['abbreviated'][dow],
        'MMMM': TIGRINYA_MONTHS_WIDE[jmonth],
        'MMM': TIGRINYA_MONTHS_ABBREVIATED[jmonth],
        'MM': "%02d" % jmonth,
        'M': "%d" % jmonth,
        'dd': "%02d" % jday,
        'd': "%d" % jday,
        'yyyy': "%04d" % jyear,
        'yy': "%02d" % (jyear % 100),
        'G': locale.eras['abbreviated'][1],
    }
    try:
        return locale.date_formats[format].format % sub_dict
    except KeyError, err:
        raise ValueError("Date format %s not defined" % err)

def format_date(date=None, format='medium', locale=None):
    """
    Format date using the server's locale
    as specified in :file:`settings.py`.
    Uses the Julian calendar for Ethiopian dates
    (language codes "ti" and "am") and the Gregorian
    calendar for other dates.

    :param date: Date to format
    :type date: :cls:`datetime.date`
    :param format: "short", "medium", "long", "full"
    :type format: :cls:`str`
    :param locale: The locale to use (defaults to server locale
                   as specified in :cls:`settings.LANGUAGE_CODE`
    :type locale: :cls:`str`
    """

    assert format in ('short','medium','long','full'),\
        "Format must be 'short', 'medium', 'long', or 'full'"
        
    if locale is None:
        locale = settings.LANGUAGE_CODE
        
    l = Locale.parse(locale)
    if l.language in ('am','ti'):
        # For our purposes, we assume that Amaharic means 
        # Tigrinya. This is because CC+ is only used in 
        # Tigrinya-speaking regions for now and Django does
        # not support the "ti" language code, so we use "am"
        # to mean "Tigrinya".
        return _format_date_ethiopian(date, format)

    else: 
        return babel.dates.format_date(date, format, settings.LANGUAGE_CODE)

def format_time(time=None, format='medium', tzinfo=None, locale=None):
    """Alias to :func:`babel.dates.format_time` which
    defaults to the Django locale
    """
    if locale is None:
        locale = Locale.parse(settings.LANGUAGE_CODE)
    if tzinfo is None:
        tzinfo = pytz.timezone(settings.TIME_ZONE)

    return babel.dates.format_time(time, format, tzinfo, locale)

def format_datetime(datetime_in=None, format='medium', locale=None):
    if locale is None:
        locale = Locale.parse(settings.LANGUAGE_CODE)

    # Borrowed from babel
    return babel.dates.get_datetime_format(format, locale=locale)\
        .replace('{0}', format_time(datetime_in, format, locale=locale))\
        .replace('{1}', format_date(datetime_in, format, locale=locale))
    
