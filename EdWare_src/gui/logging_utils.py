# Meant to be used as a library! #!/usr/bin/python

# * **************************************************************** **
#
# File: logging_utils.py
# Desc: Utilities for logging. Includes:
#       setup_root - initialises the root logger with two handlers
# Note:
#
# Author: Brian Danilko, Likeable Software (brian@likeablesoftware.com)
#
# Copyright 2006, 2014, 2015, 2016 Microbric Pty Ltd.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License (in the docs/licenses directory)
# for more details.
#
# * **************************************************************** */


import logging, logging.handlers
import types
import sys

## *:---------------------------------------------------------------
# setup_root() - setup the root logger to output to the console and a file

def setup_root(console_level = logging.INFO, fname = "/tmp/python.log", file_level = logging.DEBUG, threads=False):

    logger = logging.getLogger()
    logger.setLevel(logging.NOTSET) # Handle everything!

    # Make 2 handlers, 1 to a file with everything, 1 to the console with less
    console_log = logging.StreamHandler()
    console_log.setLevel(console_level)
    console_log.setFormatter(logging.Formatter("%(name)-12s: %(levelname)-8s %(message)s"))

    file_log = logging.handlers.RotatingFileHandler(fname, 'a', 100000, 2)
    file_log.setLevel(file_level)
    if (threads):
        file_log.setFormatter(logging.Formatter("%(asctime)s P:%(process)#x/%(thread)#x | %(name)-12s: %(levelname)-8s %(message)s"))
    else:
        file_log.setFormatter(logging.Formatter("%(asctime)s | %(name)-12s: %(levelname)-8s %(message)s"))

    logger.addHandler(console_log)
    logger.addHandler(file_log)

    logger.info("*** Root logger setup to console and file:%s ***" % (fname))


def dump_object(obj, name='', level=logging.DEBUG):
    filt = [types.MethodType]
    logging.log(level, "dump_object %s (%r)" % (name, obj))
    dir_data = dir(obj)
    data = {}

    for d in dir_data:
        if ((d in ("__module__", "__doc__")) or
            (not d.startswith("__"))):

            temp = getattr(obj, d, None)
            filter_out = False
            if (temp is not None):
                filter_out = False
                for f in filt:
                    if (type(temp) is f):
                        filter_out = True
                        break

                if (not filter_out):
                    data[d] = temp

    logging.log(level, "-- %s" % (data))


class Error_reporter(object):
    def __init__(self):
        self.errors = 0
        self.contexts = {}
        self.throw_on_error = True
        self.exit_on_error = True

        global last_error_reporter
        last_error_reporter = self

    def set_context(self, line, context):
        # remove trailing newlines and ws
        context = context.strip(' \t\n')
        if (not context):
            return

        self.contexts[line] = context

        # clear lower contexts
        new_contexts = {}
        for k in self.contexts.keys():
            if (k <= line):
                new_contexts[k] = self.contexts[k]

        self.contexts = new_contexts

    def set_throw_on_error(self, flag):
        self.throw_on_error = flag

    def set_exit_on_error(self, flag):
        self.exit_on_error = flag

    def set_error_implication(self, implication):
        self.error_implication = implication

    def report_error(self, message):
        if (not self.exit_on_error and not self.throw_on_error):
            self.errors += 1
            message = "Error (count: %d) %s" % (self.errors, message)
        else:
            message = "%s" % (message)

        ctxts = self.contexts.keys()
        ctxts.sort()
        for c in ctxts:
            message += "\n  [context:%d - %s]" % (c, self.contexts[c])

        logging.warn(message)

        if (self.throw_on_error):
            raise SyntaxError, message

        if (self.exit_on_error):
            sys.exit(5)



# * **************************************************************** **
# Test Stub

class test_class1(object):
    def __init__(self):
        self.a = 12
        self.b = 32

class test_class2(test_class1):
    def __init__(self):
        self.x = 33;
        self.y = 44;


def test_stub():
    setup_root()

    logger = logging.getLogger("test.stub")
    logger.debug("Test debug")
    logger.info("Test info")
    logger.warning("Test warning")
    logger.error("Test error")
    logger.critical("Test critical")

    tc2 = test_class2()
    dump_object(tc2, 'tc2', logging.INFO)

    logging.shutdown()


# * **************************************************************** **
# Handling running this directly

if __name__ == '__main__':
    test_stub()
