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

from .iface import ManualStart, MissingAnnotationException, unset
from .source import Builder, Class, Factory, Instance
import logging

log = logging.getLogger(__name__)
assert ManualStart
assert MissingAnnotationException

def types(*deptypes, **kwargs):
    def g(f):
        f.di_deptypes = deptypes
        if 'this' in kwargs:
            f.di_owntype = kwargs['this']
        return f
    return g

class UnsatisfiableRequestException(Exception): pass

class DI:

    log = log # Tests may override.
    depthunit = '>'

    def __init__(self, parent = None):
        self.typetosources = {}
        self.allsources = [] # Old-style classes won't be registered against object.
        self.parent = parent

    def addsource(self, source):
        for type in source.types:
            try:
                self.typetosources[type].append(source)
            except KeyError:
                self.typetosources[type] = [source]
        self.allsources.append(source)

    def removesource(self, source):
        for type in source.types:
            self.typetosources[type].remove(source)
        self.allsources.remove(source)

    def addclass(self, clazz):
        self.addsource(Class(clazz, self))
        if hasattr(clazz, 'start'):
            from .start import starter
            self.addclass(starter(clazz))
        for name in dir(clazz):
            m = getattr(clazz, name)
            if hasattr(m, 'di_deptypes') and hasattr(m, 'di_owntype'):
                assert '__init__' != name
                self.addsource(Builder(clazz, m, self))

    def addinstance(self, instance, type = None):
        self.addsource(Instance(instance, instance.__class__ if type is None else type, self))

    def addfactory(self, factory):
        self.addsource(Factory(factory, self))

    def add(self, obj):
        if hasattr(obj, 'di_owntype'):
            addmethods = self.addfactory,
        elif hasattr(obj, '__class__'):
            clazz = obj.__class__
            if clazz == type: # It's a non-fancy class.
                addmethods = self.addclass,
            elif isinstance(obj, type): # It's a fancy class.
                addmethods = self.addclass, self.addinstance
            else: # It's an instance.
                addmethods = self.addinstance,
        else: # It's an old-style class.
            addmethods = self.addclass,
        for m in addmethods:
            m(obj)
        return addmethods

    def all(self, type):
        return self._all(type, self.depthunit)

    def _all(self, type, depth):
        return [source(depth) for source in self.typetosources.get(type, [])]

    def __call__(self, clazz):
        return self._one(clazz, unset, self.depthunit)

    def _one(self, clazz, default, depth):
        if list == type(clazz):
            componenttype, = clazz
            return self._all(componenttype, depth) # XXX: Allow empty list?
        objs = self._all(clazz, depth)
        if not objs:
            if default is not unset:
                return default # XXX: Check ancestors first?
            if self.parent is not None:
                return self.parent._one(clazz, default, depth)
        if 1 != len(objs):
            raise UnsatisfiableRequestException("Expected 1 object of type %s but got: %s" % (clazz, len(objs)))
        return objs[0]

    def start(self):
        started = []
        for source in self.allsources:
            try:
                source.tostarted() and started.append(source)
            except:
                for t in reversed(started): # Don't unroll previous batches.
                    t.tostopped()
                raise

    def stop(self):
        for source in reversed(self.allsources):
            source.tostopped()

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.discardall()

    def discardall(self):
        for source in reversed(self.allsources):
            source.discard()

    def createchild(self):
        return self.__class__(self) # FIXME: Ensure self is thread-safe.
