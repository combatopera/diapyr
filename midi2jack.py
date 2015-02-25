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

from __future__ import division
from pym2149.initlogging import logging
from pym2149.jackclient import JackClient, configure
from pym2149.nod import Block
from pym2149.midi import Midi
from pym2149.config import getprocessconfig, Config
from pym2149.channels import Channels
from pym2149.boot import createdi
from pym2149.iface import Chip, Stream
from pym2149.minblep import MinBleps
from pym2149.di import types
from pym2149.util import awaitinterrupt
from pym2149.timer import Timer, SimpleTimer
from pym2149.ym2149 import ClockInfo
from pym2149.bg import Background

log = logging.getLogger(__name__)

class SyncTimer(SimpleTimer):

    @types(Stream, MinBleps, ClockInfo)
    def __init__(self, stream, minbleps, clockinfo):
        self.naiverate = clockinfo.implclock
        SimpleTimer.__init__(self, self.naiverate)
        self.buffersize = stream.buffersize
        self.naivex = 0
        self.bufferx = 0
        self.minbleps = minbleps

    def blocksforperiod(self, refreshrate):
        wholeperiodblock, = SimpleTimer.blocksforperiod(self, refreshrate)
        naiveN = wholeperiodblock.framecount
        while naiveN:
            naiven = min(naiveN, self.minbleps.getminnaiven(self.naivex, self.buffersize - self.bufferx))
            yield Block(naiven)
            self.bufferx = (self.bufferx + self.minbleps.getoutcount(self.naivex, naiven)) % self.buffersize
            self.naivex = (self.naivex + naiven) % self.naiverate
            naiveN -= naiven

class MidiPump(Background):

    @types(Config, Midi, Channels, MinBleps, Stream, Chip, Timer)
    def __init__(self, config, midi, channels, minbleps, stream, chip, timer):
        Background.__init__(self, config)
        self.updaterate = config.updaterate
        self.midi = midi
        self.channels = channels
        self.minbleps = minbleps
        self.stream = stream
        self.chip = chip
        self.timer = timer

    def __call__(self):
        frame = 0
        while not self.quit:
            # TODO: For best mediation, advance note-off events that would cause instantaneous polyphony.
            for event in self.midi.iterevents():
                log.debug("%s @ %s -> %s", event, frame, event(self.channels, frame))
            self.channels.updateall(frame)
            for block in self.timer.blocksforperiod(self.updaterate):
                self.stream.call(block)
                self.channels.applyrates()
                frame += 1

def main():
  config = getprocessconfig()
  di = createdi(config)
  di.add(Midi)
  di.add(JackClient)
  di.start()
  try:
        configure(di)
        di.start()
        di.add(Channels)
        log.info(di(Channels))
        stream = di(Stream)
        log.debug("JACK block size: %s or %.3f seconds", stream.buffersize, stream.buffersize / config.outputrate)
        di.add(SyncTimer)
        di.add(MidiPump)
        di.start()
        awaitinterrupt(config)
  finally:
        di.stop()

if '__main__' == __name__:
  main()
