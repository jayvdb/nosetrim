
"""A nose plugin that reports only unique exceptions

This is a plugin for [http://somethingaboutorange.com/mrl/projects/nose/ nosetests], a discovery based test runner for [http://python.org/ python].

If you're hacking deep inside your codebase and you break a core component you're probably going to see your test suite blow up a zillion times with the same error.  Instead, you can run your tests with --trim-errors to see only the unique exception types.  The output you get will look like...

{{{
======================================================================
ERROR: test.deep_inside.mymodule.test
----------------------------------------------------------------------
Traceback (most recent call last):
...
AttributeError

----------------------------------------------------------------------
+ 58 more
----------------------------------------------------------------------
}}}

==Install==
`easy_install nosetrim`

or ... check out the source, cd into the root and type:

`python setup.py develop`

to create a link to the latest version.

"""

import os, logging, sys
from nose.plugins import Plugin
from unittest import _WritelnDecorator, TestResult
from nose.result import TextTestResult, ln

log = logging.getLogger('nose.plugins.trim')

_errormap = {}

class NoseTrim(Plugin):
    """reports only unique exceptions"""
    
    name = 'trim'
    enabled = False
    trimmed_stream = None
    
    def add_options(self, parser, env=os.environ):
        super(NoseTrim, self).add_options(parser, env)
        env_opt = "NOSE_TRIM_ERRORS"
        parser.add_option('--trim-errors', 
                    action='store_true', 
                    dest=self.enableOpt,
                    default=env.get(env_opt),
                    help="Enable plugin %s: %s [%s]" %
                          (self.__class__.__name__, self.help(), env_opt))
        
    def configure(self, options, conf):
        global _errormap
        
        super(NoseTrim, self).configure(options, conf)
        if not self.enabled:
            return
        
        ## eeek.  voluminus akimbo, me seweth patches
        # to get into the guts of the text result:
        import nose.core
        self._SalvagedTextTestResult = nose.core.TextTestResult
        nose.core.TextTestResult = TrimmedTextResult
        
        # init the cache :
        _errormap = {}

    def finalize(self, result):
        """Called after all report output, including output from all plugins,
        has been sent to the stream. Use this to print final test
        results. Return None to allow other plugins to continue
        printing, any other value to stop them.
        """
        import nose.core
        nose.core.TextTestResult = self._SalvagedTextTestResult
        
        

class TrimmedTextResult(TextTestResult):
    """A patched up version of nose.result.TextTestResult.
    
    working with Jason to try and get proper plugin hooks to accomplish this 
    same thing without the monkey business.
    """
    def __init__(self, *args,**kw):
        super(TrimmedTextResult, self).__init__(*args,**kw)
        self._error_lookup = {}
        self._failure_lookup = {}
        
    def _isNewErr(self, err):
        etype, val, tb = err
        ename = etype.__name__
        if ename in _errormap:
            _errormap[ename] += 1
            return False
        _errormap[ename] = 1
        return True
            
    def addError(self, test, err):
        if self._isNewErr(err):
            super(TrimmedTextResult, self).addError(test, err)
        else:
            super(TrimmedTextResult, self).addSkip(test)
            
        self._error_lookup[len(self.errors)-1] = err[0].__name__
        
    def addFailure(self, test, err):
        if self._isNewErr(err):
            super(TrimmedTextResult, self).addFailure(test, err)
        else:
            super(TrimmedTextResult, self).addSkip(test)
            
        self._failure_lookup[len(self.failures)-1] = err[0].__name__

    def printErrors(self):
        if self.dots or self.showAll:
            self.stream.writeln()
        
        # shall I explain this wackiness?
        # unittest throws away the context of exception names in its infinite 
        # wisdom.  so ... we instead have to keep a map of error/failure indexes 
        # to exception names.  yay!
        
        def get_error_count(lookup, index):
            if index in lookup:
                ename = lookup[index]
                return _errormap[ename]
                
        self.printErrorList('ERROR', self.errors,
                    lambda i: get_error_count(self._error_lookup, i))
        self.printErrorList('FAIL', self.failures,
                    lambda i: get_error_count(self._failure_lookup, i))
                    
    def printErrorList(self, flavor, errors, get_error_count):
        i = 0
        for test, err, capt in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln("%s: %s" % (flavor,self.getDescription(test)))
            self.stream.writeln(self.separator2)
            self.stream.writeln("%s" % err)
            count = get_error_count(i)
            if count:
                self.stream.writeln(self.separator2)
                self.stream.writeln("+ %s more" % (count-1))
                self.stream.writeln(self.separator2)
            if capt is not None and len(capt):
                self.stream.writeln(ln('>> begin captured stdout <<'))
                self.stream.writeln(capt)
                self.stream.writeln(ln('>> end captured stdout <<'))
            i += 1
            