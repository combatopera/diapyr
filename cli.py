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
import sys, logging, getopt
from pym2149.ym2149 import YM2149, defaultscale

log = logging.getLogger(__name__)

class Config:

  @staticmethod
  def uniqueoption(options, keys, defaultval, xform):
    vals = [v for k, v in options if k in keys]
    if not vals:
      return defaultval
    v, = vals
    return xform(v)

  @staticmethod
  def booleanoption(options, keys):
    for k, _ in options:
      if k in keys:
        return True
    return False

  def __init__(self):
    options, self.args = getopt.getopt(sys.argv[1:], 's:p1', ['scale=', 'pause', 'once'])
    self.scale = self.uniqueoption(options, ('-s', '--scale'), defaultscale, int)
    self.pause = self.booleanoption(options, ('-p', '--pause'))
    self.once = self.booleanoption(options, ('-1', '--once'))

  def createchip(self, nominalclock, **kwargs):
    chip = YM2149(scale = self.scale, pause = self.pause, **kwargs)
    chip.clock = int(round(nominalclock * self.scale / 8))
    if self.scale != defaultscale:
      log.debug("Clock adjusted to %s for non-standard scale.", chip.clock)
    return chip
