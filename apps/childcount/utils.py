#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
# maintainer: ukanga

from datetime import datetime

def month_end(date):
    
    """Get end of the month date 
    
    date - any datetime object
    
    returns end of month date
    
    """
    
    for n in (31,30,28):
        try:
            return date.replace(day=n)
        except: pass
    return date

def next_month(date):
    
    """Get next month's date
    
    date - any datetime object
    
    returns next month's date
    
    """
    
    if date.day > 28:
        day     = 28
    else:
        day     = date.day
    if date.month == 12:
        month   = 1
        year    = date.year + 1
    else:
        month   = date.month + 1
        year    = date.year
        
    return date.replace(day=day, month=month, year=year)
    
def day_start(date):
    
    """Get start of day datetime object
    
    date - any datetime object
    
    returns start of day datetime object
    
    """
    
    t   = date.time().replace(hour=0,minute=1)
    return datetime.combine(date.date(), t)

def day_end(date):
    
    """Get end of day datetime object
    
    date - any datetime object
    
    returns end of day datetime object
    
    """
    
    t   = date.time().replace(hour=23,minute=59)
    return datetime.combine(date.date(), t)
