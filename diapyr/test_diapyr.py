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

from __future__ import division
from .diapyr import DI, types
from unittest import TestCase

class TestDI(TestCase):

    maxDiff = None

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
        self.assertEqual((di.addinstance,), di.add(Str('hmm')))
        self.assertEqual([Str('hmm')], di.all(Str))
        self.assertEqual([], di.all(Unicode))
        self.assertEqual([Str('hmm')], di.all(Basestring))
        self.assertEqual([], di.all(list))
        self.assertEqual((di.addinstance,), di.add(Unicode('hmmm')))
        self.assertEqual([Str('hmm')], di.all(Str))
        self.assertEqual([Unicode('hmmm')], di.all(Unicode))
        self.assertEqual([Str('hmm'), Unicode('hmmm')], di.all(Basestring))
        self.assertEqual([], di.all(list))

    def test_simpleinjection(self):
        di = DI()
        class Hmm:
            @types(str)
            def __init__(self, dep):
                self.dep = dep
        self.assertEqual((di.addclass,), di.add(Hmm))
        self.assertEqual((di.addinstance,), di.add('hmm'))
        hmm = di(Hmm)
        self.assertEqual('hmm', hmm.dep)
        self.assertIs(hmm, di(Hmm))

    def test_metaclass(self):
        di = DI()
        class HasVal(type): pass
        try:
            localz = locals()
            exec('class Impl(metaclass = HasVal): pass', globals(), localz)
            Impl = localz['Impl']
        except:
            class Impl:
                __metaclass__ = HasVal
        Impl.val = 'implval'
        class Hmm:
            @types(HasVal)
            def __init__(self, hasval):
                self.val = hasval.val
        self.assertEqual((di.addclass, di.addinstance), di.add(Impl))
        self.assertEqual((di.addclass,), di.add(Hmm))
        hmm = di(Hmm)
        self.assertEqual('implval', hmm.val)

    def test_factory(self):
        di = DI()
        class I: pass
        class N(int): pass
        class P(int): pass
        @types(int, this = I)
        def factory(n):
            return N(n) if n < 0 else P(n)
        self.assertEqual((di.addfactory,), di.add(factory))
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
        di.start()
        self.assertEqual(['A.start'], events)
        di.add(B)
        di.start() # Should only start new stuff.
        self.assertEqual(['A.start', 'B.start'], events)
        di.start() # Nothing more to be done.
        self.assertEqual(['A.start', 'B.start'], events)
        di.stop()
        self.assertEqual(['A.start', 'B.start', 'B.stop', 'A.stop'], events)
        di.stop() # Should be idempotent.
        self.assertEqual(['A.start', 'B.start', 'B.stop', 'A.stop'], events)

    def test_startdoesnotinstantiatenonstartables(self):
        class KaboomException(Exception): pass
        class Kaboom:
            @types()
            def __init__(self): raise KaboomException
            def stop(self): pass # Not significant.
        di = DI()
        di.add(Kaboom)
        di.start() # Should do nothing.
        try:
            di(Kaboom)
            self.fail('Expected a KaboomException.')
        except KaboomException:
            pass # Expected.

    class BadStart(Eventful):

        class BadStartException(Exception): pass

        def start(self): raise self.BadStartException

    def test_unrollduetobadstart(self):
        class A(self.OK): pass
        class B(self.OK): pass
        class C(self.OK): pass
        events = []
        di = DI()
        di.add(events)
        di.add(A)
        di.start()
        self.assertEqual(['A.start'], events)
        di.add(B)
        di.add(C)
        di.add(self.BadStart)
        try:
            di.start()
            self.fail('Expected a BadStartException.')
        except self.BadStart.BadStartException:
            pass # Expected.
        self.assertEqual(['A.start', 'B.start', 'C.start', 'C.stop', 'B.stop'], events)
        di.stop()
        self.assertEqual(['A.start', 'B.start', 'C.start', 'C.stop', 'B.stop', 'A.stop'], events)

    class BadStop(OK):

        class BadStopException: pass

        def stop(self): raise self.BadStopException

    def debug(self, *args):
        self.debugs.append(args)

    def error(self, *args, **kwargs):
        self.errors.append([args, kwargs])

    def test_stoperrorislogged(self):
        self.debugs = [] # Never mind.
        self.errors = events = []
        di = DI()
        di.log = self
        di.add(events)
        di.add(self.OK)
        di.add(self.BadStop)
        di.start()
        self.assertEqual(['OK.start', 'BadStop.start'], events)
        di.stop()
        self.assertEqual([
            'OK.start',
            'BadStop.start',
            [('Failed to stop an instance of %s:', "%s.%s" % (self.BadStop.__module__, self.BadStop.__name__)), {'exc_info': True}],
            'OK.stop',
        ], events)

    def test_logging(self):
        self.debugs = []
        class A:
            @types()
            def __init__(self): pass
        class B:
            @types([A])
            def __init__(self, v): pass
        class C(object):
            @types(B)
            def __init__(self, b): pass
            @types(A)
            def __init(self, a): pass
        di = DI()
        di.log = self
        di.add(A)
        di.add(B)
        di.add(C)
        di(C)
        self.assertEqual([
            ("%s Request: %s", '>', 'diapyr.test_diapyr.C'),
            ("%s Request: %s", '>>', 'diapyr.test_diapyr.B'),
            ("%s Request: %s", '>>>', 'diapyr.test_diapyr.A'),
            ("%s %s: %s", '>>>', 'Instantiate', 'diapyr.test_diapyr.A'),
            ("%s %s: %s", '>>', 'Instantiate', 'diapyr.test_diapyr.B'),
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
        childb = di.createchild()
        childb.add(B)
        childc = di.createchild()
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
