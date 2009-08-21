# coding=utf-8

def nothing(obj):
    return obj.connection.identity

def intl2dom1(obj):
    ''' removes first 2 chars. targets US-like numbers +1 xxx'''
    return obj.connection.identity[2:]

def intl2dom2(obj):
    ''' removes first 3 chars. targets EU-like numbers: +22 xxxx'''
    return obj.connection.identity[3:]

def intl2dom3(obj):
    ''' removes first 2 chars. targets Africa-like numbers +223 xxx to xxx'''
    return obj.connection.identity[4:]

def intl2dom1zero(obj):
    ''' replace first 2 chars with 0. '''
    return '0' + obj.connection.identity[2:]

def intl2dom2zero(obj):
    ''' replace first 3 chars with 0. France model: +33xxxx to 0xxxx'''
    return '0' + obj.connection.identity[3:]

def intl2dom3zero(obj):
    ''' replace first 4 chars with 0.''' 
    return '0' + obj.connection.identity[4:]

