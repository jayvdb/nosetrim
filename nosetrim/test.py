
import re
from nose.tools import eq_
import sys, os, nose, subprocess
from unittest import TestCase
import pkg_resources
from tempdir import TempDir

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
    if sys.executable and sys.version_info >= (2, 7):
        test_program = [sys.executable, '-m', 'nose']
    else:
        test_program = ['nosetests']
    
    def makeSuite(self):
        """must return the full path to a directory to test."""
        raise NotImplementedError
    
    def _makeNose(self):
        """returns a NoseStream object."""         
        return NoseStream( subprocess.Popen(self._args, 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.STDOUT, 
                                    cwd=self.suitepath, env=self.env, bufsize=1,
                                    universal_newlines=True))
                                
    def setUp(self):
        """runs nosetests within a directory named self.suitepath
        """  
        if not self.env:  
            self.env = dict([(k,v) for k,v in os.environ.items()])
        self._args = self.test_program + [self.activate_opt]
        if self.addargs:
            self._args.extend(self.addargs)
        if self.debuglog:
            self._args.append('--debug=%s' % self.debuglog)
        if not self.suitepath:
            self.suitepath = self.makeSuite()
            if isinstance(self.suitepath, TempDir):
                # keep a reference to self.suitepath so it is not destroyed
                self.temp_dir = self.suitepath
                self.suitepath = self.suitepath.name
        self.nose = self._makeNose()
    
class NoseStream(object):
    """An interface into the nosetests process.
    
    This provides a way to "scrape" the textual output produced by your plugin 
    to make sure that it's behaving correctly at the highest level possible.  
    This may be helpful for proving exact behavior, running simple "smoke 
    tests", and testing your plugin with other plugins.
    
    expects to receive an instance of subprocess.Popen
    
    Keyword Arguments
    -----------------
    - debug
      
      - if True (default) output of the test run will go to stdout
    
    Example of usage
    ----------------
    
    Create a test suite::
    
        >>> d = TempDir()
        >>> with open(os.path.join(d.name, "test_bad.py"), 'w') as f:
        >>>     f.write(
        ...         "def test_bad(): raise ValueError") #doctest: +ELLIPSIS
        '/.../test_bad.py'
        >>> nose = NoseStream(subprocess.Popen(['nosetests'],
        ...                     stdout=subprocess.PIPE,
        ...                     stderr=subprocess.STDOUT,
        ...                     cwd=d.name))
        ... 
        >>> nose.debug = False
        >>> assert "ValueError" in nose
        >>> for line in nose:
        ...     if line.startswith("ERROR"):
        ...         print line
        ...
        ERROR: test.test_bad.test_bad
    
    
    """
    def reset_buffer(self):
        self.buffer[:] = []
        
    def __init__(self, proc, debug=True):
        self.proc = proc
        self.debug = debug
        self._returncode = None
        self.buffer = []

    @property
    def returncode(self):
        if self._returncode is None:
            list(iter(self))
        return self._returncode
    
    def __contains__(self, value):
        for line in self:
            if value in line:
                return True
        return False
    
    ##
    # pad output with a little visual offset for clarity:
    def _startDebugOut(self):
        if self.debug: sys.stdout.write("\n\\\n")
    def _debugLineOut(self, line):
        if self.debug: sys.stdout.write( "".join(("    ", line, "\n")) )
    def _endDebugOut(self):
        if self.debug: sys.stdout.write("/\n")
        
    def __iter__(self):
        """yields each line.rstrip() of output
        
        output is stdout + stderr unless Popen was configured otherwise
        """
        self._startDebugOut()

        for line in self.buffer:
            self._debugLineOut(line)
            yield line

        if self._returncode is None:
            for line in self.proc.stdout:
                clean_line = line.rstrip()
                self.buffer.append(clean_line)
                self._debugLineOut(clean_line)
                yield clean_line
            self._returncode = self.proc.wait()

        self._endDebugOut()

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
        d = TempDir()
        with open(os.path.join(d.name, 'test_many_errors.py'), 'w') as f:
            f.write("""
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
        return d
        
    def test_suite(self):
        assert 'AssertionError' in self.nose
        assert 'ValueError' in self.nose
        
        assert self.nose.returncode != 0

class TestTrim(WithSimpleSuite, NoseTrimTest, TestCase):
    pass

class TestTrimVerbose(WithSimpleSuite, NoseTrimTest, TestCase):
    addargs = ['--verbose']
    
class TestTrimNonDupes(NoseTrimTest, TestCase):
    def makeSuite(self):
        d = TempDir()
        with open(os.path.join(d.name, 'test_lone_error.py'), 'w') as f:
            f.write("""
def test_lone_error():
    raise AssertionError
""")
        return d
    
    def test_non_dupes(self):
        assert "+ 0 more" not in self.nose
