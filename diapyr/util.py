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

@singleton
class outerzip:

    class Session:

        def __init__(self, iterables):
            self.iterators = [iter(i) for i in iterables]

        def row(self):
            self.validrow = len(self.iterators)
            for i in self.iterators:
                try:
                    yield next(i)
                except StopIteration:
                    self.validrow -= 1
                    yield

    def __call__(self, *iterables):
        session = self.Session(iterables)
        while True:
            values = tuple(session.row())
            if not session.validrow:
                break
            yield values

def enum(*lists):
    def d(cls):
        cls.enum = v = []
        for args in lists:
            obj = cls(*args)
            setattr(cls, args[0], obj)
            v.append(obj)
        return cls
    return d
