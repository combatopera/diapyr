# Copyright 2014, 2018, 2019, 2020 Andrzej Cichocki

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

from .util import enum, innerclass, invokeall, ispy2, outerzip, singleton
from functools import partial
from unittest import TestCase

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
    class PlainInner(object):

        a = 100

    class FancyInner2(FancyInner): pass

    class PlainInner2(PlainInner):

        a = 200

class TestCommon(TestCase):

    def _fancyinner(self, name):
        inner = getattr(MyOuter('mybaz'), name)('myfoo')
        # Check _frobimpl is found:
        self.assertEqual(('myfoo', 'mybar1', 'mybaz'), inner.frob('mybar1'))
        self.assertEqual(('myfoo', 'mybar2', 'mybaz'), inner.frob('mybar2'))
        # Check inner __getattr__ behaviour is otherwise preserved:
        self.assertEqual('QUUX', inner.quux)
        with self.assertRaises(AttributeError) as cm:
            inner.lol
        self.assertEqual(('lol',), cm.exception.args)

    def test_fancyinner(self):
        self._fancyinner('FancyInner')

    def test_fancyinner2(self):
        self._fancyinner('FancyInner2')

    def _plaininner(self, name):
        inner = getattr(MyOuter('whatever'), name)()
        self.assertEqual('hidden', inner.foo)
        with self.assertRaises(AttributeError) as cm:
            inner.quux
        self.assertEqual(("'%s' object has no attribute 'quux'" % name,), cm.exception.args)
        return inner

    def test_plaininner(self):
        inner = self._plaininner('PlainInner')
        self.assertEqual(100, inner.a)

    def test_plaininner2(self):
        inner = self._plaininner('PlainInner2')
        self.assertEqual(200, inner.a)

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

    def test_singleton(self):
        @singleton
        def t(): return 100
        self.assertEqual(100, t)

    def test_outerzip(self):
        self.assertEqual([], list(outerzip()))
        self.assertEqual([], list(outerzip([])))
        self.assertEqual([], list(outerzip([], [])))
        self.assertEqual([(None, 0, 3), (None, 1, None), (None, 2, None)], list(outerzip([], [0, 1, 2], [3])))

    def test_enum(self):
        @enum(['p', 5], ['q'])
        class X:
            def __init__(self, key, val = None):
                self.key = key
                self.val = val
        self.assertEqual('p', X.p.key)
        self.assertEqual(5, X.p.val)
        self.assertEqual('q', X.q.key)
        self.assertEqual(None, X.q.val)
        self.assertEqual([X.p, X.q], X.enum)

    def test_enum2(self):
        @enum(['anum', 1], ['enum', 2], ['znum', 3])
        class X:
            def __init__(self, name, num):
                self.name = name
                self.num = num
        self.assertEqual('anum', X.anum.name)
        self.assertEqual(1, X.anum.num)
        self.assertEqual('enum', X.enum.name) # Overrides the list.
        self.assertEqual(2, X.enum.num)
        self.assertEqual('znum', X.znum.name)
        self.assertEqual(3, X.znum.num)

def good(value):
    return value

def bad(e):
    raise e

class TestInvokeAll(TestCase):

    def test_generator(self):
        with self.assertRaises(TypeError):
            invokeall(_ for _ in [])

    def test_happypath(self):
        self.assertEqual([], invokeall([]))
        self.assertEqual([50], invokeall([partial(good, 50)]))
        self.assertEqual([100, 200], invokeall((partial(good, 100), partial(good, 200))))

    def test_1fail(self):
        e1 = Exception(1)
        with self.assertRaises(Exception) as cm:
            invokeall([partial(good, 123), partial(bad, e1)])
        self.assertIs(e1, cm.exception)

    def test_2fails(self):
        e1 = Exception(1)
        e2 = Exception(2)
        with self.assertRaises(Exception) as cm:
            invokeall([partial(bad, e1), partial(good, 456), partial(bad, e2)])
        self.assertIs(e2, cm.exception)
        if not ispy2:
            self.assertIs(e1, cm.exception.__context__)

    def test_3fails(self):
        e1 = Exception(1)
        e2 = Exception(2)
        e3 = Exception(3)
        with self.assertRaises(Exception) as cm:
            invokeall([partial(bad, e1), partial(bad, e2), partial(bad, e3)])
        # When cm.exception is printed these will appear in the order they were raised:
        self.assertIs(e3, cm.exception)
        if not ispy2:
            self.assertIs(e2, cm.exception.__context__)
            self.assertIs(e1, cm.exception.__context__.__context__)

    class X(Exception): pass

    class Y(Exception): pass

    def _existingcontext(self, f):
        with self.assertRaises(self.Y) as cm:
            f()
        if not ispy2:
            self.assertIsInstance(cm.exception.__context__, KeyError)
            self.assertIsInstance(cm.exception.__context__.__context__, self.X)
            self.assertIsInstance(cm.exception.__context__.__context__.__context__, IndexError)
            self.assertIs(None, cm.exception.__context__.__context__.__context__.__context__)

    def test_existingcontextflat(self):
        def f():
            try:
                [][0]
            except:
                try:
                    raise self.X
                except:
                    try:
                        {}[0]
                    except:
                        raise self.Y
        self._existingcontext(f)

    def test_existingcontext(self):
        def f():
            try:
                [][0]
            except:
                raise self.X
        def g():
            try:
                {}[0]
            except:
                raise self.Y
        with self.assertRaises(self.X) as cm:
            f()
        if not ispy2:
            self.assertIsInstance(cm.exception.__context__, IndexError)
            self.assertIs(None, cm.exception.__context__.__context__)
        with self.assertRaises(self.Y) as cm:
            g()
        if not ispy2:
            self.assertIsInstance(cm.exception.__context__, KeyError)
            self.assertIs(None, cm.exception.__context__.__context__)
        self._existingcontext(lambda: invokeall([f, g]))

    def test_rethrowwithcontext(self):
        if ispy2:
            return
        from concurrent.futures import ThreadPoolExecutor
        def f():
            try:
                [][0]
            except:
                raise self.X
        def g():
            try:
                {}[0]
            except:
                raise self.Y
        with ThreadPoolExecutor() as e:
            self._existingcontext(lambda: invokeall([e.submit(x).result for x in [f, g]]))
