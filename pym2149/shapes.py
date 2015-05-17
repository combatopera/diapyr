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

from __future__ import division
from nod import BufNode
from buf import DiffRing
import math

loopsize = 1024
log2 = math.log(2)

def level5toamp(level):
  return 2 ** ((level - 31) / 4)

def amptolevel5(amp):
  return 31 + 4 * math.log(amp) / log2

def level4to5(level4):
    return level4 * 2 + 1 # Observe 4-bit 0 is 5-bit 1.

def cycle(unit): # Unlike itertools version, we assume unit can be iterated more than once.
    unitsize = len(unit)
    if 0 != loopsize % unitsize:
        raise Exception("Unit size %s does not divide %s." % (unitsize, loopsize))
    for _ in xrange(loopsize // unitsize):
        for x in unit:
            yield x

tonediffs = DiffRing(cycle([1, 0]), 0, BufNode.bindiffdtype)

def sinering(steps): # Like saw but unlike triangular, we use steps for a full wave.
    unit = []
    minamp = level5toamp(0)
    for i in xrange(steps):
        amp = minamp + (1 - minamp) * (math.sin(2 * math.pi * i / steps) + 1) / 2
        unit.append(round(amptolevel5(amp)))
    return DiffRing(cycle(unit), 0, BufNode.zto127diffdtype)

# FIXME: Implement this properly.
sinusdiffs = DiffRing([13, 14, 15, 14, 13, 11, 0, 11] * (loopsize // 8), 0, BufNode.zto127diffdtype)
