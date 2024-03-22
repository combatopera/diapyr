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

from contextlib import contextmanager
from importlib import import_module
import os, sys

def _patch(modulename, setup):
    try:
        import_module(modulename).setup = setup
    except Exception as e: # XXX: Not BaseException?
        sys.stderr.write("Leave %s unpatched: %s\n" % (modulename, e))

class Stack(list):

    def setup(self, **kwargs):
        self.append(kwargs)

@contextmanager
def _outtoerr():
    stdout, sys.stdout = sys.stdout, sys.stderr
    try:
        yield
    finally:
        sys.stdout = stdout

def main():
    sys.argv.pop(0)
    path = sys.argv[0]
    fields = set(sys.argv[1:])
    sys.argv[1:] = ['--name'] # Invoke as little around setup itself as possible.
    sys.path.insert(0, os.path.dirname(path))
    stack = Stack()
    for m in 'distutils.core', 'setuptools':
        _patch(m, stack.setup)
    try:
        with _outtoerr(), open(path) as f:
            exec(f.read(), dict(__name__ = '__main__', __file__ = path))
    except BaseException as e: # Such as SystemExit for bad interpreter version.
        sys.stdout.write(repr(e))
    else:
        setupkwargs, = stack
        sys.stdout.write(repr({k: v for k, v in setupkwargs.items() if k in fields}))

if ('__main__' == __name__):
    main()
