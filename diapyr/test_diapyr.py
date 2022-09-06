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

from __future__ import division
from .diapyr import DI, types
from .iface import MissingAnnotationException, UnsatisfiableRequestException
from .start import Started
from .util import ispy2
from unittest import TestCase
import sys

def _add(di, obj):
    methods = list(di._addmethods(obj))
    di.add(obj)
    return methods

class DebugCase(TestCase):

    maxDiff = None

    def debug(self, *args):
        self.debugs.append(args)

class TestDI(DebugCase):

    def test_instances(self):
        class Basestring:
            def __init__(self, text): self.text = text
            def __eq__(self, that): return self.text == that.text
        class Str(Basestring): pass
        class Unicode(Basestring): pass
        di = DI()
        self.assertEqual([], di.all(Str))
        self.assertEqual([], di.all(Unicode))
        self.assertEqual([], di.all(Basestring))
        self.assertEqual([], di.all(list))
        self.assertEqual([di.addinstance], _add(di, Str('hmm')))
        self.assertEqual([Str('hmm')], di.all(Str))
        self.assertEqual([], di.all(Unicode))
        self.assertEqual([Str('hmm')], di.all(Basestring))
        self.assertEqual([], di.all(list))
        self.assertEqual([di.addinstance], _add(di, Unicode('hmmm')))
        self.assertEqual([Str('hmm')], di.all(Str))
        self.assertEqual([Unicode('hmmm')], di.all(Unicode))
        self.assertEqual([Str('hmm'), Unicode('hmmm')], di.all(Basestring))
        self.assertEqual([], di.all(list))

    def test_simpleinjection(self):
        class Hmm:
            @types(str)
            def __init__(self, dep):
                self.dep = dep
        di = DI()
        self.assertEqual([di.addclass], _add(di, Hmm))
        self.assertEqual([di.addinstance], _add(di, 'hmm'))
        hmm = di(Hmm)
        self.assertEqual('hmm', hmm.dep)
        self.assertIs(hmm, di(Hmm))

    def test_metaclass(self):
        class HasVal(type): pass
        try:
            localz = locals()
            exec('''class Impl(metaclass = HasVal):
    @types()
    def __init__(self): raise Exception''', globals(), localz)
            Impl = localz['Impl']
        except SyntaxError:
            class Impl:
                __metaclass__ = HasVal
                @types()
                def __init__(self): raise Exception # pragma: no cover
        Impl.val = 'implval'
        class Hmm:
            @types(HasVal)
            def __init__(self, hasval):
                self.val = hasval.val
        di = DI()
        self.assertEqual([di.addinstance, di.addclass], _add(di, Impl))
        self.assertEqual([di.addclass], _add(di, Hmm))
        self.assertEqual('implval', di(Hmm).val)
        del Impl.__init__
        self.assertEqual([di.addinstance], list(di._addmethods(Impl)))

    def test_factory(self):
        class I: pass
        class N(int): pass
        class P(int): pass
        @types(int, this = I)
        def factory(n):
            return N(n) if n < 0 else P(n)
        di = DI()
        self.assertEqual([di.addfactory], _add(di, factory))
        di.add(5)
        i = di(I) # No spin as DI thinks factory is I only.
        self.assertIs(P, i.__class__)
        self.assertEqual(5, i)

    def test_optional(self):
        class A:
            @types()
            def __init__(self): pass
        class B:
            @types()
            def __init__(self): pass
        class Opt:
            @types(A, B)
            def __init__(self, a, b = 123):
                self.a = a
                self.b = b
        di = DI()
        di.add(A)
        di.add(Opt)
        opt = di(Opt)
        self.assertIs(A, opt.a.__class__)
        self.assertEqual(123, opt.b)
        di.add(B)
        self.assertEqual(123, di(Opt).b) # It's cached.
        di = DI()
        di.add(A)
        di.add(B)
        di.add(Opt)
        opt = di(Opt)
        self.assertIs(A, opt.a.__class__)
        self.assertIs(B, opt.b.__class__)

    class Eventful:

        @types(list)
        def __init__(self, events): self.events = events

    class OK(Eventful):

        def start(self): self.events.append(self.__class__.__name__ + '.start')

        def stop(self): self.events.append(self.__class__.__name__ + '.stop')

    def test_lifecycle(self):
        class A(self.OK): pass
        class B(self.OK): pass
        events = []
        di = DI()
        di.add(events)
        di.add(A)
        di.all(Started)
        self.assertEqual(['A.start'], events)
        di.add(B)
        di.all(Started) # Should only start new stuff.
        self.assertEqual(['A.start', 'B.start'], events)
        di.all(Started) # Nothing more to be done.
        self.assertEqual(['A.start', 'B.start'], events)
        di.discardall()
        self.assertEqual(['A.start', 'B.start', 'B.stop', 'A.stop'], events)
        di.discardall() # Should be idempotent.
        self.assertEqual(['A.start', 'B.start', 'B.stop', 'A.stop'], events)

    def test_startdoesnotinstantiatenonstartables(self):
        class KaboomException(Exception): pass
        class Kaboom:
            @types()
            def __init__(self): raise KaboomException
            def stop(self): pass # Not significant.
        di = DI()
        di.add(Kaboom)
        di.all(Started) # Should do nothing.
        with self.assertRaises(KaboomException):
            di(Kaboom)

    class BadStart(Eventful):

        class BadStartException(Exception): pass

        def start(self): raise self.BadStartException

    def test_nounrollduetobadstart(self):
        class A(self.OK): pass
        class B(self.OK): pass
        class C(self.OK): pass
        events = []
        di = DI()
        di.add(events)
        di.add(A)
        di.all(Started)
        self.assertEqual(['A.start'], events)
        di.add(B)
        di.add(C)
        di.add(self.BadStart)
        with self.assertRaises(self.BadStart.BadStartException):
            di.all(Started)
        self.assertEqual(['A.start', 'B.start', 'C.start'], events)
        di.discardall()
        self.assertEqual(['A.start', 'B.start', 'C.start', 'C.stop', 'B.stop', 'A.stop'], events)

    class BadStop(OK):

        class BadStopException(Exception): pass

        def stop(self): raise self.BadStopException

    def error(self, *args, **kwargs):
        self.errors.append([args, kwargs])

    def test_stoperrorispropagated(self):
        self.debugs = [] # Never mind.
        self.errors = events = []
        di = DI()
        di.log = self
        di.add(events)
        di.add(self.OK)
        di.add(self.BadStop)
        di.all(Started)
        self.assertEqual(['OK.start', 'BadStop.start'], events)
        with self.assertRaises(self.BadStop.BadStopException):
            di.discardall()
        self.assertEqual([
            'OK.start',
            'BadStop.start',
            'OK.stop',
        ], events)

    def test_logging(self):
        self.debugs = []
        class Z:
            @types()
            def __init__(self): pass
        class A:
            @types(Z)
            def __init__(self, z): pass
        class B: pass
        class BImpl(B):
            @types([A])
            def __init__(self, v): pass
        class C(object):
            @types(B)
            def __init__(self, b): pass
            @types(A)
            def __init(self, a): pass
        di = DI()
        di.log = self
        di.add(Z)
        di.add(A)
        di.add(BImpl)
        di.add(C)
        di(C)
        self.assertEqual([
            ("%s Request: %s%s", '>', 'diapyr.test_diapyr.C', ''),
            ("%s Request: %s%s", '>>', 'diapyr.test_diapyr.BImpl', '(diapyr.test_diapyr.B)'),
            ("%s Request: %s%s", '>>', 'diapyr.test_diapyr.A', ''),
            ('%s Request: %s%s', '>>>', 'diapyr.test_diapyr.Z', ''),
            ('%s %s: %s', '>>>', 'Instantiate', 'diapyr.test_diapyr.Z'),
            ("%s %s: %s", '>>', 'Instantiate', 'diapyr.test_diapyr.A'),
            ("%s %s: %s", '>>', 'Instantiate', 'diapyr.test_diapyr.BImpl'),
            ("%s %s: %s", '>', 'Instantiate', 'diapyr.test_diapyr.C'),
            ("%s Enhance: %s", '>', 'diapyr.test_diapyr.C'),
        ], self.debugs)

    def test_child(self):
        class A:
            @types()
            def __init__(self): pass
        class B:
            @types(A)
            def __init__(self, a): self.a = a
        class C:
            @types(A)
            def __init__(self, a): self.a = a
        di = DI()
        di.add(A)
        childb = DI(di)
        childb.add(B)
        childc = DI(di)
        childc.add(C)
        b = childb(B)
        c = childc(C)
        self.assertIs(b.a, c.a)
        self.assertIs(b.a, di(A))

    def test_setupmethods(self):
        class A(object):
            s = ''
            @types(str)
            def __init__(self, s): self.s += s
            @property
            def uhoh(self): raise Exception # pragma: no cover
        class X(A):
            both = None
            @types(int)
            def __init(self, i, j = 200):
                self.i = i
                self.j = j
            @types()
            def zzz1(self): raise Exception # pragma: no cover
        class C(X):
            @types()
            def __init(self): self.both = self.s, self.i
            @types()
            def zzz1(self): self.z1 = self.both
            @types()
            def zzz2(self): self.z2 = self.both
        di = DI()
        di.add('hello')
        di.add(100)
        di.add(C)
        c = di(C)
        self.assertEqual('hello', c.s)
        self.assertEqual(100, c.i)
        self.assertEqual(200, c.j)
        self.assertEqual(('hello', 100), c.both)
        self.assertEqual(None, c.z1)
        self.assertEqual(('hello', 100), c.z2)

    def test_with(self):
        disposed = []
        class A:
            @types()
            def __init__(self): pass
            def dispose(self): disposed.append(self)
        with DI() as di:
            di.add(A)
            di(A)
        self.assertEqual([A], [o.__class__ for o in disposed])

    def test_returnnone(self):
        v = []
        class Result: pass
        @types(this = Result)
        def r(): v.append(len(v))
        di = DI()
        di.add(r)
        self.assertEqual([], v)
        self.assertEqual(None, di(Result))
        self.assertEqual([0], v)
        self.assertEqual(None, di(Result))
        self.assertEqual([0], v)

    def test_buildsystem(self):
        class B: pass
        class X: pass
        class Y: pass
        class A:
            @types(B)
            def __init__(self, b): self.v = b.v / 2
            @types(this = X)
            def makex(self): return self.v
        class BImpl(B):
            @types()
            def __init__(self): self.v = 3
            @types(X, this = Y)
            def makey(self, x): return x, self.v
        di = DI()
        di.add(A)
        di.add(BImpl)
        self.assertEqual((1.5, 3), di(Y))

    def test_toomany(self):
        allow = False
        class A:
            @types()
            def __init__(self): assert allow
        class B(A): pass
        class C(A): pass
        di = DI()
        di.add(B)
        di.add(C)
        with self.assertRaises(UnsatisfiableRequestException) as cm:
            di(A)
        self.assertEqual(("Expected 1 object of type %s but got: 2" % A,), cm.exception.args)
        allow = True
        self.assertEqual([B, C], [x.__class__ for x in di.all(A)])

    def test_notenough(self):
        class A: pass
        di = DI()
        with self.assertRaises(UnsatisfiableRequestException) as cm:
            di(A)
        self.assertEqual(("Expected 1 object of type %s but got: 0" % A,), cm.exception.args)

    def test_discardinstance(self):
        discards = []
        def intercept():
            realdiscard() # Does nothing.
            discards.append('yay')
        with DI() as di:
            di.add(100)
            src, = di.allsources
            realdiscard = src.discard
            src.discard = intercept
        self.assertEqual(['yay'], discards)

    def test_addbadclass(self):
        class A:
            def __init__(self): pass
        di = DI()
        with self.assertRaises(MissingAnnotationException):
            di.add(A)

    def test_addbadclass2(self):
        class A: pass
        di = DI()
        with self.assertRaises(MissingAnnotationException):
            di.add(A)

    def test_objasbuilder(self):
        class B: pass # XXX: If a result type has builders, should they be added?
        class A:
            @types(this = B)
            def mkb(self): return 100
        di = DI()
        di.add(A())
        self.assertEqual(100, di(B))

    def test_keywordonlyarg(self):
        if not ispy2:
            exec('''log = object()
@types(str, this = int)
def f(*args, log = log):
    return [*args, log]
di = DI()
di.add('woo')
di.add(f)
self.assertEqual(['woo', log], di(int))''')

    def test_getexceptionindispose(self):
        class C:
            @types()
            def __init__(self): pass
            def dispose(self): self.x = sys.exc_info()[1]
        class X(Exception): pass
        x = X()
        with self.assertRaises(X), DI() as di:
            di.add(C)
            c = di(C)
            raise x
        self.assertIs(x, c.x)

    def test_getexceptionindisposeviaexitstack(self):
        if ispy2:
            return
        from contextlib import ExitStack
        class C:
            @types()
            def __init__(self): pass
            def dispose(self): self.x = sys.exc_info()[1]
        class X(Exception): pass
        x = X()
        with self.assertRaises(X), ExitStack() as stack:
            di = stack.enter_context(DI())
            di.add(C)
            c = di(C)
            raise x
        self.assertIs(x, c.x)

    def test_lastresort(self):
        log = object()
        class L: pass
        class A:
            @types(L)
            def __init__(self, log = log):
                self.log = log
        with DI() as di:
            with DI(di) as di2:
                di2.add(A)
                self.assertIs(log, di2(A).log)
            l = L()
            di.add(l)
            with DI(di) as di3:
                di3.add(A)
                self.assertIs(l, di3(A).log)

class TestProxy(DebugCase):

    class B: pass

    def setUp(self):
        self.debugs = []
        self.disposed = []
        class D:
            def dispose(this): self.disposed.append(this)
        class A(D):
            @types()
            def __init__(self): pass
        class BImpl(D, self.B):
            @types(A)
            def __init__(self, a): self.a = a
        class C(D):
            @types(self.B)
            def __init__(self, b): self.b = b
        self.A = A
        self.BImpl = BImpl
        self.C = C

    def test_exitcontext(self):
        with DI() as di:
            di.log = self
            di.add(self.A)
            di.add(self.C)
            with DI(di) as subdi:
                subdi.log = self
                subdi.add(self.BImpl)
                subdi.join(self.BImpl, False)
                c = di(self.C)
                b = di(self.B)
                a = di(self.A)
                self.assertIs(c.b, b)
                self.assertIs(b.a, a)
                self.assertIs(b, subdi(self.B))
                self.assertFalse(self.disposed)
            self.assertEqual([b], self.disposed)
        self.assertEqual([b, c, a], self.disposed)

    def test_discardall(self):
        with DI() as di:
            di.log = self
            di.add(self.A)
            di.add(self.C)
            subdi = DI(di)
            subdi.log = self
            subdi.add(self.BImpl)
            subdi.join(self.BImpl)
            c = di(self.C)
            b = di(self.B)
            a = di(self.A)
            self.assertIs(c.b, b)
            self.assertIs(b.a, a)
            self.assertIs(b, subdi(self.B))
            self.assertFalse(self.disposed)
        self.assertEqual([b, c, a], self.disposed)

    def tearDown(self):
        self.assertEqual([
            ('%s Request: %s%s', '>', 'diapyr.test_diapyr.C', ''),
            ('%s Request: %s%s', '>>', 'diapyr.test_diapyr.BImpl', '(diapyr.test_diapyr.B)'),
            ('%s Request: %s%s', '>>>', 'diapyr.test_diapyr.A', ''),
            ('%s %s: %s', '>>>', 'Instantiate', 'diapyr.test_diapyr.A'),
            ('%s %s: %s', '>>', 'Instantiate', 'diapyr.test_diapyr.BImpl'),
            ('%s %s: %s', '>', 'Instantiate', 'diapyr.test_diapyr.C'),
            ('Dispose: %s', 'diapyr.test_diapyr.BImpl'),
            ('Dispose: %s', 'diapyr.test_diapyr.C'),
            ('Dispose: %s', 'diapyr.test_diapyr.A'),
        ], self.debugs)
