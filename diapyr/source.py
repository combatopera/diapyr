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

from .iface import Special, unset
from .match import wrap
import inspect

class Source:

    def __init__(self, type, di):
        self.types = set()
        def addtype(type):
            self.types.add(type)
            for base in type.__bases__:
                if base not in self.types:
                    addtype(base)
        addtype(type)
        self.typelabel = Special.gettypelabel(type)
        self.type = type
        self.di = di

class Instance(Source):

    def __init__(self, instance, type, di):
        Source.__init__(self, type, di)
        self.instance = instance

    def make(self, depth, trigger):
        return self.instance

    def discard(self):
        pass # TODO: Test this if possible.

class Creator(Source):

    instance = unset

    def __init__(self, callable, di):
        Source.__init__(self, self.getowntype(callable), di)
        self.callable = callable

    def make(self, depth, trigger):
        if self.instance is unset:
            self.di.log.debug("%s Request: %s%s", depth, self.typelabel, '' if trigger == self.type else "(%s)" % Special.gettypelabel(trigger))
            args = self.toargs(*self.getdeptypesanddefaults(self.callable), depth = "%s%s" % (depth, self.di.depthunit))
            self.di.log.debug("%s %s: %s", depth, self.action, self.typelabel)
            instance = self.callable(*args)
            self.enhance(instance, depth)
            self.instance = instance
        return self.instance

    def toargs(self, deptypes, defaults, depth):
        if defaults:
            args = [t.di_get(self.di, unset, depth) for t in deptypes[:-len(defaults)]]
            return args + [t.di_get(self.di, default, depth) for t, default in zip(deptypes[-len(defaults):], defaults)]
        return [t.di_get(self.di, unset, depth) for t in deptypes]

    def discard(self):
        if self.instance is not unset:
            if hasattr(self.instance, 'dispose'):
                self.di.log.debug("Dispose: %s", self.typelabel)
                try:
                    self.instance.dispose()
                except:
                    self.di.log.error("Failed to dispose an instance of %s:", self.typelabel, exc_info = True)
            self.instance = unset

class Class(Creator):

    action = 'Instantiate'

    @staticmethod
    def getowntype(clazz):
        return clazz

    def getdeptypesanddefaults(self, clazz):
        ctor = clazz.__init__
        return ctor.di_deptypes, inspect.getargspec(ctor).defaults

    def enhance(self, instance, depth):
        methods = {}
        for name in dir(self.callable):
            if '__init__' != name:
                m = getattr(self.callable, name)
                if hasattr(m, 'di_deptypes') and not hasattr(m, 'di_owntype'):
                    methods[name] = m
        if methods:
            self.di.log.debug("%s Enhance: %s", depth, self.typelabel)
            for ancestor in reversed(self.callable.mro()):
                for name in dir(ancestor):
                    if name in methods:
                        m = methods.pop(name)
                        m(instance, *self.toargs(m.di_deptypes, inspect.getargspec(m).defaults, depth))

class Factory(Creator):

    action = 'Fabricate'

    @staticmethod
    def getowntype(factory):
        return factory.di_owntype

    @staticmethod
    def getdeptypesanddefaults(factory):
        return factory.di_deptypes, inspect.getargspec(factory).defaults

    def enhance(self, instance, depth):
        pass

class Builder(Creator):

    action = 'Build'

    def __init__(self, receivertype, method, di):
        Creator.__init__(self, method, di)
        self.receivermatch = wrap(receivertype)

    @staticmethod
    def getowntype(factory):
        return factory.di_owntype

    def getdeptypesanddefaults(self, factory):
        return (self.receivermatch,) + factory.di_deptypes, inspect.getargspec(factory).defaults

    def enhance(self, instance, depth):
        pass
