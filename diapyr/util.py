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

class Proxy(object):

    def __getattr__(self, name):
        try:
            return getattr(self._enclosinginstance, name)
        except AttributeError:
            superclass = super(Proxy, self)
            try:
                supergetattr = superclass.__getattr__
            except AttributeError:
                raise AttributeError("'%s' object has no attribute '%s'" % (self._cls.__name__, name))
            return supergetattr(name)

def innerclass(cls):
    def getproxy(enclosinginstance):
        class Inner(Proxy, cls):
            _cls = cls
            _enclosinginstance = enclosinginstance
        return Inner
    return property(getproxy)

def singleton(t):
    return t()
