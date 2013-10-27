from __future__ import division
import sys, logging, getopt
from pym2149.util import Session
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

  def __init__(self):
    options, self.args = getopt.getopt(sys.argv[1:], 's:', ['scale='])
    self.scale = self.uniqueoption(options, ('-s', '--scale'), defaultscale, int)

  def createchipandsession(self, nominalclock):
    clock = nominalclock * self.scale / 8 # Observe may be non-integer.
    if self.scale != defaultscale:
      log.debug("Clock adjusted to %.3f for non-standard scale.", clock)
    return YM2149(scale = self.scale), Session(clock)