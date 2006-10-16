#!/usr/bin/python

class CurrentException(Exception):
    """Base class for all Current exceptions."""

    pass

class CurrentRPCError(CurrentException):
    pass

class CurrentDB(CurrentException):
    pass

class CurrentSQLite(CurrentDB):
    pass

class CurrentSession(CurrentException):
    pass

class ConfigurationError(CurrentException):
    pass

class CurrentUser(CurrentException):
    pass

class CurrentOUError(CurrentException):
    pass
