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

from pym2149.initlogging import logging
from pym2149.timer import Timer
from pym2149.ymformat import ymopen
from pym2149.jackclient import JackClient, configure
from pym2149.config import getprocessconfig
from pym2149.vis import Roll
from pym2149.boot import createdi
from pym2149.iface import Chip, Stream, YMFile
from pym2149.di import types
import threading, time

log = logging.getLogger(__name__)

class Player:

    @types(YMFile, Chip, Roll, Timer, Stream)
    def __init__(self, ymfile, chip, roll, timer, stream):
        self.ymfile = ymfile
        self.chip = chip
        self.roll = roll
        self.timer = timer
        self.stream = stream

    def start(self):
        self.quit = False
        self.thread = threading.Thread(target = self)
        self.thread.start()

    def __call__(self):
        for frame in self.ymfile:
            if self.quit:
                break
            frame(self.chip)
            self.roll.update()
            for b in self.timer.blocksforperiod(self.ymfile.framefreq):
                self.stream.call(b)

    def stop(self):
        self.quit = True
        self.thread.join()

def main():
  config = getprocessconfig()
  config.inpath, = config.positional
  with JackClient(config) as jackclient:
    f = ymopen(config)
    try:
      for info in f.info:
        log.info(info)
      config.contextclock = f.clock
      di = createdi(config)
      configure(di)
      chip = di(Chip)
      stream = di(Stream)
      try:
        timer = Timer(chip.clock) # TODO LATER: Support sync with jack block schedule.
        config.contextpianorollheight = f.framefreq
        roll = Roll(config, chip)
        di.add(f)
        di.add(roll)
        di.add(timer)
        di.add(Player)
        di.start()
        try:
          while True:
            time.sleep(1)
        except KeyboardInterrupt:
          log.debug('Caught interrupt, shutting down.')
        di.stop()
      finally:
        stream.close()
    finally:
      f.close()

if '__main__' == __name__:
  main()
