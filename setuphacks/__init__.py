# Copyright 2013, 2014, 2015, 2016, 2017, 2020, 2022 Andrzej Cichocki

# This file is part of pyven.
#
# pyven is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyven is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyven.  If not, see <http://www.gnu.org/licenses/>.

from . import fakesetup
from traceback import format_exception_only
import os, subprocess, sys

class SetupException(Exception): pass

def getsetupkwargs(setuppath, fields):
    cwd, = (dict(cwd = d) if d else {} for d in [os.path.dirname(setuppath)])
    setupkwargs = eval(subprocess.check_output([sys.executable, fakesetup.__file__, os.path.basename(setuppath)] + fields, **cwd))
    if isinstance(setupkwargs, BaseException):
        # Can't simply propagate SystemExit for example:
        raise SetupException(format_exception_only(setupkwargs.__class__, setupkwargs)[-1].rstrip())
    return setupkwargs
