#!/usr/bin/python

# This module is designed to take in a string that's formatted to
# look roughly like a valid Python data type, and to store the
# resulting construct and make it available.
# Eventually, it will support Much Embeddedness.

# Copyright 2000 (c) John Berninger
# I assume this is released under the GPL, since he submitted it to me 
# for inclusion in Current. -- Hunter Matthews

import types
import exceptions
import pprint
import string

class Error(exceptions.Exception):
    pass

class ParseError(Error):
    """ We encountered an error in the parser, but the string we're parsing
    /appears/ to be valid"""
    pass

class FormatError(Error):
    """ The string we're parsing is invalid"""
    pass

class SupportError(Error):
    """ The string we're parsing is valid as far as we've gotten, but you're
    trying to use a Python data type that we don't yet support."""
    pass

class ConstructParser:
    def __init__(self, string=''):
        self._source = string

    def setDefaultType(self, defType):
        self._defaultType = defType

    def setParseString(self, string):
        self._source = string
        
    def _parsingDone(self):
        return self._currPos >= len(self._source)

    # Start of the actual parse routines
    def parseIt(self):
        self._currPos = 0
        token = self._getToken()
        while token in string.whitespace:
            token = self._getToken()
        if token in ('\'', '"'):
            self._result = self._parseString(token)
        elif token == '[':
            self._result = self._parseList()
        elif token == '{':
            self._result = self._parseDict()
        elif token == '(':
            self._result = self._parseTuple()
        elif token in string.digits:
            self._result = self._parseNum()
        assert self._parsingDone()
        return self._result
    
    def _parseTuple(self):
        # We've seen the open paren.  tuple vals are separated by
        # commas and whitespace
        tmp = [] # We have to make a list first, then change it into a tuple
                 # just before we return
        item = None
        token = ' '
        while 1:
            token = self._getToken()
            if token == ',':
                tmp.append(item)
                item = None
            elif token == ')':
                tmp.append(item)
                break
            elif token == '[':
                item = self._parseList()
            elif token == '{':
                item = self._parseDict()
            elif token == '(':
                item = self._parseTuple()
            elif token in ('\'', '"'):
                item = self._parseString()
            elif token in string.digits:
                self._putToken()
                item = self._parseNum()
            elif token in string.whitespace:
                continue

        # Now we convert the list into a tuple
        strng=''
        for i in range(len(tmp)):
            strng = strng + str(tmp[i]) + ','

        newtmp = eval(strng)

        return newtmp            


    def _parseNum(self):
        # Nums must be delimited by whitespace, ':', ','
        # We know we've seen and put back an int, so we're good so far.
        decimal = 0
        tmp = ''
        while 1:
            token = self._getToken()
            if token in (string.whitespace):
                continue
            if token in (':,}])'):
                self._putToken()
                break
            if not token in (string.digits + '.'):
                raise FormatError
            if token == '.':
                decimal = 1
            tmp = tmp + token
        if decimal == 1:
            return string.atof(tmp)
        else:
            return string.atoi(tmp)

    def _parseDict(self):
        # We have seen the open brace.  we need to parse the key, a ':', then
        # the value.  The key can be an int or a string, the value can be
        # damn near anything.  We do NOT allow variable interpolation in either
        # key or value - that's way too hard for now.
        token = ' '
        while token in string.whitespace:
            token = self._getToken()
        if token == '(':
            key = self._parseTuple()
        elif not token in ('\'', '"'):
            self._putToken()
            key = self._parseNum()
        else:
            key = self._parseString(token)

        token = self._getToken()
        # Mke sure we see a colon, 'cause we're supposed to for a dict.
        assert token == ':'

        token = ' '
        while token in string.whitespace:
            token = self._getToken()
        if token in ('\'', '"'):
            val = self._parseString(token)
        elif token == '[':
            val = self._parseList()
        elif token == '{':
            val = self._parseDict()
        elif token == '(':
            val = self._parseTuple()
        elif token in string.digits:
            self._putToken()
            val = self._parseNum()

        # we now have the value

        token = ' '
        while token in string.whitespace:
            token = self._getToken()

        # make sure we see a close brace
        if token != '}':
            raise FormatError
        else:
            return {key:val}

    def _parseList(self):
        # We assume we've already recognized and processed a list
        # start char ('['), so we go merrily on our way.
        tmp = []  # this is the list we're returning.
        item = None # item is the current item in the list we're working on
        while 1:
            # If we're done parsing and we're at this point, the string is
            # invalid and we need to bail.  No sane error recovery yet.
            if self._parsingDone():
                raise FormatError
            token = self._getToken()
            if token == ']':
                tmp.append(item)
                return tmp
            elif token == '[':
                item = self._parseList()
            elif token == '{':
                item = self._parseDict()
            elif token in ('\'', '"'):
                item = self._parseString(token)
            elif token == '(':
                item = self._parseTuple()
            elif token == ',':
                tmp.append(item)
                item = None
            elif token in string.digits or token == ".":
                self._putToken()
                item = self._parseNum()
            elif token in string.whitespace:
                continue
        
    def _parseString(self, delimit):
        # We have seen a string delimiter, it is 'delimit'
        tmp = ''
        escape = 0
        while 1:
            token = self._getToken()
            if token == None:
                break
            elif token == delimit and escape == 0:
                break
            elif token == '\\':
                tmp = tmp + token
                escape = ( escape + 1 ) % 2
            else:
                tmp = tmp + token
        return tmp

    def _getToken(self):
        if self._currPos >= len(self._source):
            return None
        token = self._source[self._currPos]
        self._currPos = self._currPos + 1
        return token

    def _putToken(self):
        if self._currPos == 0:
            raise ParseError   # We can't go back before the start of the
                               # string!
        self._currPos = self._currPos - 1

def _main():
    # This is for testing purposes only!
    parseObject = "['dulug-7.1', '2001', {'a':['d', 'e']}, {12.4:13.2}]"
    parseObject = "(1,2,3,[1,2])"
    parseTree = ConstructParser(parseObject)
    print parseTree.parseIt()

    data = "[['dulug-7.1', '2001'], ['dulug-powertools-7.1', 'x9000']]"
    parseTree = ConstructParser(data)
    x = parseTree.parseIt()
    pprint.pprint(x)
    print type(x)
    print type(x[0])
    print type(x[1])
    print type(x[0][0])

if __name__ == '__main__':
    _main()


## BUG LIST

# 1. data = "['dulug-7.1', '2001', ]" yields
# ['dulug-7.1', '2001', None]  which isn't quite right.
#   Fixed

# 2.     data = """['dulug-7.1', '2001" ]"""  
# breaks the parser with a TypeError
#   Of course it does.  '2001" is not a valid string representation - the
#   quote close charachter must be the same as the open character.
#   """['dulug-7.1', '2001']""" works as expected.
#   I've added a test to raise a format error in the right place, I'll also
#   look at adding them to the Dict and Tuple parse routines.

# 3. some of your methods make no sense to be called outside the object -
# I've prefixed them with a single _ 
#   Not a problem.
 
# 4.  data = "[['dulug-7.1', '2001'], ['dulug-powertools-7.1', 'x9000']]"
# looks like it works fine. Patched in.
#  :)

# 5. I don't like the name getConstruct(). Is getObject() acceptable?
#  Sure - I named it getConstruct to match the class name ConstructParser,
#  but either one works

# 6. Can we change it to conform to the Current coding standard?
# IE, parser.py, class parser, etc?
#  This isn't a problem, I chose the long name to avoid any potential namespace
#  conflicts with Python iteself.

# Question:  Why are you having parseIt return the object?  I didn't want that
# routine to return anything, in case we want to add error recovery and a
# success / failure indication later.

#Bug: we can't handle tuples that aren't explicit tuples; in Python 2.x, this
# is okay, do we want to use 1.5 / 1.6 style tuples as well?
