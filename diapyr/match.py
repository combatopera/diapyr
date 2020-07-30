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

from .iface import UnsatisfiableRequestException, unset

class AllInstancesOf:

    def __init__(self, clazz):
        self.clazz = clazz

    def getall(self, di, depth):
        return [source.make(depth, self.clazz) for source in di.typetosources.get(self.clazz, [])]

    def di_get(self, di, default, depth):
        return self.getall(di, depth)

class One:

    def di_get(self, di, default, depth):
        objs = self.many(di, depth)
        if not objs:
            if default is not unset:
                return default # XXX: Check ancestors first?
            if di.parent is not None:
                return self.di_get(di.parent, default, depth)
        if 1 != len(objs):
            raise UnsatisfiableRequestException("Expected 1 object of type %s but got: %s" % (self.clazz, len(objs))) # FIXME: Untested!
        return objs[0]

class OneInstanceOf(One):

    @property
    def clazz(self):
        return self.all.clazz

    def __init__(self, clazz):
        self.all = AllInstancesOf(clazz)

    def many(self, di, depth):
        return self.all.getall(di, depth)

class ExactMatch(One):

    def __init__(self, clazz):
        self.clazz = clazz

    def many(self, di, depth):
        return [source.make(depth, self.clazz) for source in di.typetosources.get(self.clazz, []) if self.clazz == source.type]

def wrap(obj):
    if list == type(obj):
        componenttype, = obj
        return AllInstancesOf(componenttype)
    if hasattr(obj, 'di_get'):
        return obj
    return OneInstanceOf(obj)
