# Copyright 2014, 2018, 2019, 2020, 2024 Andrzej Cichocki

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

from .iface import Special
from .match import ExactMatch

class Started(Special): pass

def starter(startabletype):
    try:
        starter = startabletype.di_starter
    except AttributeError:
        pass
    else:
        match, = starter.__init__.di_deptypes
        if match.clazz == startabletype: # Otherwise it's inherited.
            return starter
    from .diapyr import types
    @types(ExactMatch(startabletype))
    def __init__(self, startable):
        startable.start()
        self.startable = startable
    def dispose(self):
        self.startable.stop() # FIXME: Untested.
    startabletype.di_starter = startedtype = type("Started[%s]" % Special.gettypelabel(startabletype), (Started,), {f.__name__: f for f in [__init__, dispose]})
    return startedtype
