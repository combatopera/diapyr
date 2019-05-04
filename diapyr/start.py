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

from . import types
import logging

log = logging.getLogger(__name__)

class Started: pass

def starter(startabletype):
    try:
        return startabletype.__dict__['di_starter']
    except KeyError:
        pass
    typelabel = "%s.%s" % (startabletype.__module__, startabletype.__name__)
    class StartedImpl(Started):
        @types([startabletype]) # TODO LATER: Shouldn't instantiate subtypes.
        def __init__(self, startables):
            startable, = (s for s in startables if s.__class__ == startabletype)
            log.debug("Starting: %s", typelabel)
            startable.start()
            self.startable = startable
        def dispose(self):
            log.debug("Stopping: %s", typelabel)
            self.startable.stop()
    startabletype.di_starter = StartedImpl
    return StartedImpl
