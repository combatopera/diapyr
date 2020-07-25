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
import inspect

class Source:

    class Static: startable, stoppable = False, False

    class Stopped: startable, stoppable = True, False

    class Started: startable, stoppable = False, True

    def __init__(self, type, di):
        self.types = set()
        def addtype(type):
            self.types.add(type)
            for base in type.__bases__:
                if base not in self.types:
                    addtype(base)
        addtype(type)
        self.typelabel = "%s.%s" % (type.__module__, type.__name__)
        # We assume stop exists if start does:
        self.lifecycle = self.Stopped if hasattr(type, 'start') and not issubclass(type, ManualStart) else self.Static
        self.di = di

    def tostarted(self):
        if self.lifecycle.startable:
            instance = self(self.di.depthunit) # Observe we only instantiate if startable.
            self.di.log.debug("Starting: %s", self.typelabel)
            instance.start() # On failure we assume state unchanged from Stopped.
            self.lifecycle = self.Started
            return True # Notify caller a transition to Started actually happened.

    def tostopped(self):
        if self.lifecycle.stoppable:
            instance = self(self.di.depthunit) # Should already exist.
            self.di.log.debug("Stopping: %s", self.typelabel)
            try:
                instance.stop()
            except:
                self.di.log.error("Failed to stop an instance of %s:", self.typelabel, exc_info = True)
            self.lifecycle = self.Stopped # Even on failure, we don't attempt to stop again.

class Instance(Source):

    def __init__(self, instance, type, di):
        Source.__init__(self, type, di)
        self.instance = instance

    def __call__(self, depth):
        return self.instance

    def discard(self):
        pass

class Creator(Source):

    voidinstance = object()

    def __init__(self, callable, di):
        Source.__init__(self, self.getowntype(callable), di)
        self.instance = self.voidinstance
        self.callable = callable

    def __call__(self, depth):
        if self.instance is self.voidinstance:
            self.di.log.debug("%s Request: %s", depth, self.typelabel)
            args = self.toargs(*self.getdeptypesanddefaults(self.callable), depth = "%s%s" % (depth, self.di.depthunit))
            self.di.log.debug("%s %s: %s", depth, self.action, self.typelabel)
            instance = self.callable(*args)
            self.enhance(instance, depth)
            self.instance = instance
        return self.instance

    def toargs(self, deptypes, defaults, depth):
        if defaults:
            args = [self.di._one(t, unset, depth) for t in deptypes[:-len(defaults)]]
            return args + [self.di._one(t, default, depth) for t, default in zip(deptypes[-len(defaults):], defaults)]
        return [self.di._one(t, unset, depth) for t in deptypes]

    def discard(self):
        if self.instance is not self.voidinstance:
            if hasattr(self.instance, 'dispose'): self.instance.dispose()
            self.instance = self.voidinstance

class Class(Creator):

    action = 'Instantiate'

    @staticmethod
    def getowntype(clazz):
        return clazz

    def getdeptypesanddefaults(self, clazz):
        ctor = getattr(clazz, '__init__')
        defaults = inspect.getargspec(ctor).defaults
        try:
            return ctor.di_deptypes, defaults
        except AttributeError:
            raise MissingAnnotationException("Missing types annotation: %s" % self.typelabel)

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
        self.receivertype = receivertype

    @staticmethod
    def getowntype(factory):
        return factory.di_owntype

    def getdeptypesanddefaults(self, factory):
        return (self.receivertype,) + factory.di_deptypes, inspect.getargspec(factory).defaults

    def enhance(self, instance, depth):
        pass
