#!/usr/bin/env python

# Copyright 2014 Andrzej Cichocki

# This file is part of pym2149.
#
# pym2149 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pym2149 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pym2149.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from pitch import Pitch

class TestPitch(unittest.TestCase):

    def test_str(self):
        self.assertEqual('C..4   ', str(Pitch(60)))
        self.assertEqual('C#.4   ', str(Pitch(61)))
        self.assertEqual('B..3   ', str(Pitch(59)))
        self.assertEqual('B..3+40', str(Pitch(59.4)))
        self.assertEqual('C..4-40', str(Pitch(59.6)))
        self.assertEqual('B..3+50', str(Pitch(59.5)))
        self.assertEqual('C..0   ', str(Pitch(12)))
        self.assertEqual('B.-1   ', str(Pitch(11)))
        self.assertEqual('B..9   ', str(Pitch(131)))
        self.assertEqual('C.10   ', str(Pitch(132)))

if __name__ == '__main__':
    unittest.main()
