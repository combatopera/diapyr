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

from .iface import UnsatisfiableRequestException, unset

class OneInstanceOf:

    def __init__(self, clazz):
        self.clazz = clazz

    def di_get(self, di, default, depth):
        objs = [source(depth) for source in di.typetosources.get(self.clazz, [])]
        if not objs:
            if default is not unset:
                return default # XXX: Check ancestors first?
            if di.parent is not None:
                return self.di_get(di.parent, default, depth)
        if 1 != len(objs):
            raise UnsatisfiableRequestException("Expected 1 object of type %s but got: %s" % (self.clazz, len(objs))) # FIXME: Untested!
        return objs[0]

class AllInstancesOf:

    def __init__(self, clazz):
        self.clazz = clazz

    def di_get(self, di, default, depth):
        return [source(depth) for source in di.typetosources.get(self.clazz, [])]

class ExactMatch:

    def __init__(self, clazz):
        self.clazz = clazz

    def di_get(self, di, default, depth):
        objs = [source(depth) for source in di.typetosources.get(self.clazz, []) if self.clazz == source.type]
        if not objs:
            if default is not unset:
                return default # XXX: Check ancestors first?
            if di.parent is not None:
                return self.di_get(di.parent, default, depth)
        if 1 != len(objs):
            raise UnsatisfiableRequestException("Expected 1 object of type %s but got: %s" % (self.clazz, len(objs))) # FIXME: Untested!
        return objs[0]

def wrap(obj):
    if list == type(obj):
        componenttype, = obj
        return AllInstancesOf(componenttype)
    if hasattr(obj, 'di_get'):
        return obj
    return OneInstanceOf(obj)
