
import re
from nose.tools import eq_
import sys, os, nose, subprocess
from unittest import TestCase
import pkg_resources
from fixture import TempIO

class PluginTester(object):
    """A mixin for testing nose plugins in their runtime environment.
    
    Subclass this and mix in unittest.TestCase to run integration/functional 
    tests on your plugin.  After setUp() the class contains an attribute, 
    self.nose, which is an instance of NoseStream.  See NoseStream docs for 
    more details
    
    Class Variables
    ---------------
    - activate_opt
    
      - the option to send nosetests to activate the plugin
     
    - suitepath
    
      - if set, this is the path of the suite to test.  otherwise, you will need 
        to use the hook, makeSuite()
      
    - debuglog

      - if not None, becomes the value of --debug=debuglog
    
    - addargs
  
      - a list of arguments to add to the nosetests command
    
    - env
    
      - optional dict of environment variables to send nosetests
      
    """
    activate_opt = None
    suitepath = None
    debuglog = False
    addargs = None
    env = {}
    _args = None
    nose = None
    
    class NoseStream(object):
        """An interface into the nosetests process.
        
        This provides a way to "scrape" the textual output produced by your 
        plugin to make sure that it is behaving correctly at the highest level 
        possible.  This may be helpful for proving exact behavior and testing 
        your plugin with other plugins.
        
        """
        def __init__(self, proc):
            self.proc = proc
        
        def inspect(self, expect_error=False, foreach_line=None):
            """inspect the result of your test run.
            
            Keyword Arguments
            -----------------
            - foreach_line
            
              - if not None, called with each line of output as the argument.  
                Designed to be used for pattern matching.
              
            - expect_error
              
              - if True, an AssertionError will be raised if the test passes.  
                Otherwise, an AssertionError is raised if the test fails 
                (default behavior).
            
            """
            # output is for debugging only, padded with a little visual offset 
            # for clarity
            sys.stdout.write("\n\\\n")
            for line in self.proc.stdout:
                if foreach_line:
                    foreach_line(line)
                sys.stdout.write( "".join(("    ", line)) )
            sys.stdout.write("/\n")
            returncode = self.proc.wait()
            if expect_error:
                assert returncode != 0
            else:
                eq_(returncode, 0)
    
    def makeSuite(self):
        """must return the full path to a directory to test."""
        raise NotImplementedError
    
    def _makeNose(self):
        """returns a NoseStream object."""         
        return self.NoseStream( subprocess.Popen(self._args, 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.STDOUT, 
                                    cwd=self.suitepath, env=self.env, bufsize=1,
                                    universal_newlines=True))
                                
    def setUp(self):
        """runs nosetests within a directory named self.suitepath
        """  
        if not self.env:  
            self.env = dict([(k,v) for k,v in os.environ.items()])
        self._args = ['nosetests', self.activate_opt]
        if self.addargs:
            self._args.extend(self.addargs)
        if self.debuglog:
            self._args.append('--debug=%s' % self.debuglog)
        if not self.suitepath:
            self.suitepath = self.makeSuite()
        self.nose = self._makeNose()

class NoseTrimTest(PluginTester):
    activate_opt = '--with-trim'
    debuglog = "nose.plugins.trim"
    
    def setUp(self):
        # it might be better to just install it directly using setuptools API?
        try:
            from nosetrim import NoseTrim
            eps = set([e.name for e in 
                        pkg_resources.iter_entry_points('nose.plugins')])
            if 'trim' not in eps:
                raise AssertionError
        except (ImportError, AssertionError):
            raise AssertionError(
                "you must first run python setup.py develop to run these tests")
                 
        PluginTester.setUp(self)

class WithSimpleSuite(object):
    """mixin that tests a simple suite."""
    def makeSuite(self):
        tmp = TempIO()
        tmp.putfile('test_many_errors.py', """
def test_assert_one():
    raise AssertionError("nope x is not y")
def test_one():
    pass
def test_assert_two():
    raise AssertionError("sory y is definitely not x")
def test_two():
    pass
def test_value_one():
    raise ValueError
def test_value_two():
    raise ValueError
def test_good_one():
    pass
def test_good_two():
    pass
""")
        os.chdir(tmp)
        return tmp
        
    def test_suite(self):
        exc_re = re.compile("^(AssertionError|ValueError)")
        saw = {}
        def watch_line(line):
            m = exc_re.search(line)
            if m:
                k = m.group(1)
                saw.setdefault(k, 0)
                saw[k] += 1
            
        self.nose.inspect(expect_error=True, foreach_line=watch_line)
        
        eq_(saw['AssertionError'], 1)
        eq_(saw['ValueError'], 1)

class TestNoseTrim(WithSimpleSuite, NoseTrimTest, TestCase):
    pass

class TestNoseTrimVerbose(WithSimpleSuite, NoseTrimTest, TestCase):
    addargs = ['--verbose']