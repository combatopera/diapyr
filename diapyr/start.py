# Copyright 2014 Andrzej Cichocki

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

import logging
from diapyr import types

log = logging.getLogger(__name__)

class Started: pass

def starter(startabletype):
    class StartedImpl(Started):
        @types(startabletype)
        def __init__(self, startable):
            startable.start()
            self.startable = startable
        def dispose(self):
            log.debug("Stopping: %s.%s", startabletype.__module__, startabletype.__name__)
            self.startable.stop()
    return StartedImpl
