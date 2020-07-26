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

from .diapyr import DI, types
from .start import starter, Started
from unittest import TestCase

class TestStarted(TestCase):

    def test_started(self):
        class A:
            @types()
            def __init__(self): pass
            def start(self):
                self.resource = 'gotcha'
        class B:
            @types(starter(A))
            def __init__(self, astarter):
                self.resource = astarter.startable.resource
        di = DI()
        di.add(A)
        di.add(B)
        self.assertEqual('gotcha', di(B).resource)

    def test_hierarchy(self):
        class A:
            @types()
            def __init__(self): pass
            def start(self): pass
        class B(A): pass
        di = DI()
        di.add(A)
        di.add(B)
        self.assertEqual([A, B], [s.startable.__class__ for s in di.all(Started)])

    def test_donotinstantiatesubclasses(self):
        class A:
            @types()
            def __init__(self):
                pass
            def start(self):
                pass
        class B(A):
            @types()
            def __init__(self):
                raise Exception('No.')
            start = None
        di = DI()
        di.add(A)
        di.add(B)
        di.all(Started)
