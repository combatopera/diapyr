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

from .iface import MissingAnnotationException, unset
from .match import AllInstancesOf, wrap
from .source import Builder, Class, Factory, Instance
from .start import Started, starter
from collections import defaultdict
import logging

log = logging.getLogger(__name__)

def types(*deptypes, **kwargs):
    def g(f):
        f.di_deptypes = tuple(wrap(t) for t in deptypes)
        if 'this' in kwargs:
            f.di_owntype = kwargs['this']
        return f
    return g

class DI:

    log = log # Tests may override.
    depthunit = '>'

    def __init__(self, parent = None):
        self.typetosources = defaultdict(list)
        self.allsources = [] # Old-style classes won't be registered against object.
        self.parent = parent

    def addsource(self, source):
        for type in source.types:
            self.typetosources[type].append(source)
        self.allsources.append(source)

    def removesource(self, source): # TODO: Untested.
        for type in source.types:
            self.typetosources[type].remove(source)
        self.allsources.remove(source)

    def addclass(self, clazz):
        try:
            clazz.__init__.di_deptypes
        except AttributeError:
            raise MissingAnnotationException("Missing types annotation: %s" % clazz)
        self.addsource(Class(clazz, self))
        for name in dir(clazz):
            m = getattr(clazz, name)
            if hasattr(m, 'di_deptypes') and hasattr(m, 'di_owntype'):
                assert '__init__' != name # TODO LATER: Check upfront.
                self.addsource(Builder(clazz, m, self))
        if getattr(clazz, 'start', None) is not None:
            self.addclass(starter(clazz))

    def addinstance(self, instance, type = None):
        self.addsource(Instance(instance, instance.__class__ if type is None else type, self))

    def addfactory(self, factory):
        self.addsource(Factory(factory, self))

    def _addmethods(self, obj):
        if hasattr(obj, 'di_owntype'):
            yield self.addfactory
        elif hasattr(obj, '__class__'):
            clazz = obj.__class__
            if clazz == type: # It's a non-fancy class.
                yield self.addclass
            elif isinstance(obj, type): # It's a fancy class.
                yield self.addinstance
                try:
                    obj.__init__.di_deptypes
                    yield self.addclass
                except AttributeError:
                    pass # Not admissible as class.
            else: # It's an instance.
                yield self.addinstance
        else: # It's an old-style class.
            yield self.addclass

    def add(self, obj):
        for m in self._addmethods(obj):
            m(obj)

    def all(self, type):
        return AllInstancesOf(type).getall(self, self.depthunit)

    def __call__(self, clazz):
        return wrap(clazz).di_get(self, unset, self.depthunit)

    def start(self):
        alreadystarted = set(s for s in self.typetosources.get(Started, []) if s.instance is not unset)
        try:
            self.all(Started)
        except:
            for source in reversed(self.typetosources.get(Started, [])):
                if source not in alreadystarted:
                    source.discard()
            raise

    def stop(self):
        for source in reversed(self.typetosources.get(Started, [])):
            source.discard()

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.discardall()

    def discardall(self):
        for source in reversed(self.allsources):
            source.discard()

    def createchild(self):
        return self.__class__(self) # FIXME: Ensure self is thread-safe.
