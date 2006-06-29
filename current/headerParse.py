#!/usr/bin/python
#
# headerParse.py - Based off of John Berninger's ConstructParser to parse
#    up2date client HTTP headers.
# Copyright 2000 - 2005 by John Berninger, Jack Neely
#
# SDG
#
# Some of this has been stolen from firstboot.
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

from types import *
import exception
import string


class ParseError(exception.CurrentException):
    """ We encountered an error in the parser, but the string we're parsing
    /appears/ to be valid"""
    pass


class FormatError(exception.CurrentException):
    """ The string we're parsing is invalid"""
    pass


class FSMParser(object):
    
    def __init__(self, string=''):
        self._source = string


    def setParseString(self, string):
        self._source = string


    def _parsingDone(self):
        return self._currPos >= len(self._source)


    def parse(self):
        """Return a list containing one or more list-like objects found
           in the header string from an up2date client."""
           
        self._currPos = 0
        result = []
        
        while not self._parsingDone():
            token = self._getToken()
            while token in string.whitespace:
                token = self._getToken()

            if self._parsingDone():
                break
            
            if token == ',':
                # A ',' occured outside the list-like construct
                if result == []:
                    raise FormatError("Unexpected ','")
            elif token == '[':
                result.append(self._parseList())
            else:
                raise FormatError("Unexpected input in parse()")
       
        if len(result) > 0 and type(result[0][0]) == ListType:
            # Parse string was a list of lists
            return result[0]

        return result
    

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
            elif token in ('\'', '"'):
                item = self._parseString(token)
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
            raise ParseError("We can't go back before the start of the string")

        self._currPos = self._currPos - 1


def __main__():
    # This is for testing purposes only!
    
    # We want to be able to handling strings of at least three formats
    test = ["['rawhide', '20050206212651'],['test', '20050119220409']",
            "[['rawhide', '20050206212651'], ['test', '20050119220409']]",
            "['test', '20050119220409']",
            ""]

    for t in test:
        print "Testing: %s" % t
        fsm = FSMParser(t)
        print fsm.parse()
    

if __name__ == '__main__':
    __main__()


