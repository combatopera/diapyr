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

from setuphacks import getsetupkwargs
from tempfile import NamedTemporaryFile
from unittest import TestCase
import os

class TestSetupRoot(TestCase):

    def test_getsetupkwargs(self):
        with NamedTemporaryFile('w') as setup:
            setup.write('''from setuptools import setup
baz = 200
setup(foo = 'bar', bar = 100, baz = baz)''')
            setup.flush()
            self.assertEqual(dict(foo = 'bar', baz = 200), getsetupkwargs(setup.name, ['foo', 'baz', 'x']))

    def test_basenameonly(self):
         with NamedTemporaryFile('w', dir = '.') as setup:
            setup.write('''from setuptools import setup
baz = 200
setup(foo = 'bar', bar = 100, baz = baz)''')
            setup.flush()
            self.assertEqual(dict(foo = 'bar', baz = 200), getsetupkwargs(os.path.basename(setup.name), ['foo', 'baz', 'x']))
