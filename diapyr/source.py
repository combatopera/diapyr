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
from .util import innerclass
try:
    from inspect import getfullargspec as getargspec
except ImportError:
    from inspect import getargspec
from itertools import chain, repeat

class Source(object):

    def __init__(self, type):
        def addtype(type):
            self.types.add(type)
            for base in type.__bases__:
                if base not in self.types:
                    addtype(base)
        self.types = set()
        addtype(type)
        self.typelabel = Special.gettypelabel(type)
        self.type = type

class Instance(Source):

    def __init__(self, instance, type):
        super(Instance, self).__init__(type)
        self.instance = instance

    def make(self, depth, trigger):
        return self.instance

    def discard(self):
        pass # TODO: Test this if possible.

class Proxy(Source):

    def __init__(self, otherdi, type, discardall):
        super(Proxy, self).__init__(type)
        self.otherdi = otherdi
        self.discardall = discardall

    def make(self, depth, trigger):
        return self.otherdi(self.type)

    def discard(self):
        if self.discardall:
            self.otherdi.discardall()

class Creator(Source):

    instance = unset

    def __init__(self, instantiator, di):
        super(Creator, self).__init__(instantiator.resulttype)
        self.instantiator = instantiator
        self.di = di

    def make(self, depth, trigger):
        if self.instance is unset:
            self.di.log.debug("%s Request: %s%s", depth, self.typelabel, '' if trigger == self.type else "(%s)" % Special.gettypelabel(trigger))
            plan = self.instantiator.Plan("%s%s" % (depth, self.di.depthunit))
            self.di.log.debug("%s %s: %s", depth, type(self.instantiator).__name__, self.typelabel)
            self.instance = plan.fire(depth)
        return self.instance

    def toargs(self, depth, deptypes, defaults):
        if defaults is None:
            defaults = ()
        return [t.di_get(self.di, default, depth) for t, default in zip(deptypes, chain(repeat(unset, len(deptypes) - len(defaults)), defaults))]

    def discard(self):
        instance, self.instance = self.instance, unset
        if instance is not unset:
            try:
                dispose = instance.dispose
            except AttributeError:
                pass
            else:
                self.di.log.debug("Dispose: %s", self.typelabel)
                dispose()

class Class(Creator):

    @innerclass
    class Instantiate(object):

        @property
        def resulttype(self):
            return self.cls

        def __init__(self, cls):
            self.cls = cls

        @innerclass
        class Plan(object):

            def __init__(self, depth):
                ctor = self.cls.__init__
                methods = {}
                for name in dir(self.cls):
                    if '__init__' != name:
                        m = getattr(self.cls, name)
                        if hasattr(m, 'di_deptypes') and not hasattr(m, 'di_owntype'):
                            methods[name] = m
                self.args = self.toargs(depth, ctor.di_deptypes, getargspec(ctor).defaults)
                self.enhancers = []
                if methods:
                    for ancestor in reversed(self.cls.mro()):
                        for name in dir(ancestor):
                            try:
                                m = methods.pop(name)
                            except KeyError:
                                pass
                            else:
                                self.enhancers.append([m, self.toargs(depth, m.di_deptypes, getargspec(m).defaults)])

            def fire(self, depth):
                instance = self.cls(*self.args)
                if self.enhancers:
                    self.di.log.debug("%s Enhance: %s", depth, self.typelabel)
                    for m, eargs in self.enhancers:
                        m(instance, *eargs)
                return instance

    def __init__(self, cls, di):
        super(Class, self).__init__(self.Instantiate(cls), di)

class Factory(Creator):

    @innerclass
    class Fabricate(object):

        @property
        def resulttype(self):
            return self.function.di_owntype

        def __init__(self, function):
            self.function = function

        @innerclass
        class Plan(object):

            def __init__(self, depth):
                self.args = self.toargs(depth, self.function.di_deptypes, getargspec(self.function).defaults)

            def fire(self, depth):
                return self.function(*self.args)

    def __init__(self, function, di):
        super(Factory, self).__init__(self.Fabricate(function), di)

class Builder(Creator):

    @innerclass
    class Build(object):

        @property
        def resulttype(self):
            return self.method.di_owntype

        def __init__(self, receivertype, method):
            self.receivermatch = wrap(receivertype)
            self.method = method

        @innerclass
        class Plan(object):

            def __init__(self, depth):
                self.args = self.toargs(depth, (self.receivermatch,) + self.method.di_deptypes, getargspec(self.method).defaults)

            def fire(self, depth):
                return self.method(*self.args)

    def __init__(self, receivertype, method, di):
        super(Builder, self).__init__(self.Build(receivertype, method), di)
