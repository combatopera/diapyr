# Copyright 2014, 2018, 2019 Andrzej Cichocki

# This file is part of diapyr.
#
# diapyr is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# diapyr is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with diapyr.  If not, see <http://www.gnu.org/licenses/>.

from .util import innerclass
import unittest

class MyOuter:

    foo = 'hidden'
    myprop = property(lambda self: self.baz, lambda self, value: setattr(self, 'baz', value))

    @innerclass
    class FancyInner(object):

        def __init__(self, foo):
            self.foo = foo

        def frob(self, bar):
            return self._frobimpl(self.foo, bar)

        def __getattr__(self, name):
            if 4 == len(name):
                return name.upper()
            raise AttributeError(name)

    def __init__(self, baz):
        self.baz = baz

    def _frobimpl(self, foo, bar):
        return foo, bar, self.baz

    @innerclass
    class PlainInner(object): pass

class TestCommon(unittest.TestCase):

    def test_fancyinner(self):
        inner = MyOuter('mybaz').FancyInner('myfoo')
        # Check _frobimpl is found:
        self.assertEqual(('myfoo', 'mybar1', 'mybaz'), inner.frob('mybar1'))
        self.assertEqual(('myfoo', 'mybar2', 'mybaz'), inner.frob('mybar2'))
        # Check inner __getattr__ behaviour is otherwise preserved:
        self.assertEqual('QUUX', inner.quux)
        with self.assertRaises(AttributeError) as cm:
            inner.lol
        self.assertEqual(('lol',), cm.exception.args)

    def test_plaininner(self):
        inner = MyOuter('whatever').PlainInner()
        self.assertEqual('hidden', inner.foo)
        with self.assertRaises(AttributeError) as cm:
            inner.quux
        self.assertEqual(("'PlainInner' object has no attribute 'quux'",), cm.exception.args)

    def test_propertyaccess(self):
        outer = MyOuter('hmm')
        inner = outer.PlainInner()
        self.assertEqual('hmm', outer.myprop)
        self.assertEqual('hmm', inner.myprop)
        outer.myprop = 'hmm2'
        self.assertEqual('hmm2', outer.myprop)
        self.assertEqual('hmm2', inner.myprop)
        inner.myprop = 'hmm3'
        self.assertEqual('hmm2', outer.myprop) # XXX: Possible to propagate value?
        self.assertEqual('hmm3', inner.myprop)
