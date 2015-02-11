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
from pym2149.out import configure
from pym2149.nod import Block
from pym2149.midi import Midi
from pym2149.config import getprocessconfig
from pym2149.channels import Channels
from pym2149.boot import createdi
from pym2149.iface import Chip, Stream
from pym2149.minblep import MinBleps
from pym2149.di import types
from pym2149.util import awaitinterrupt
from ymplayer import Background

log = logging.getLogger(__name__)

class MidiPump(Background):

    @types(Midi, Channels, MinBleps, Stream, Chip)
    def __init__(self, midi, channels, minbleps, stream, chip):
        self.midi = midi
        self.channels = channels
        self.minbleps = minbleps
        self.stream = stream
        self.chip = chip

    def __call__(self):
        naivex = 0
        frame = 0
        while not self.quit:
            # TODO: For best mediation, advance note-off events that would cause instantaneous polyphony.
            for event in self.midi.iterevents():
                log.debug("%s @ %s -> %s", event, frame, event(self.channels, frame))
            self.channels.updateall(frame)
            # Make min amount of chip data to get one JACK block:
            naiven = self.minbleps.getminnaiven(naivex, self.stream.size)
            self.stream.call(Block(naiven))
            self.channels.applyrates()
            naivex = (naivex + naiven) % self.chip.clock
            frame += 1

def main():
  config = getprocessconfig('outpath')
  di = createdi(config)
  di.add(Midi)
  configure(di)
  di.start()
  try:
        stream = di(Stream)
        di.add(Channels)
        channels = di(Channels)
        log.info(channels)
        blocksizeseconds = stream.size / config.outputrate
        log.debug("JACK block size: %s or %.3f seconds", stream.size, blocksizeseconds)
        log.info("Chip update rate for arps and slides: %.3f Hz", 1 / blocksizeseconds)
        di.add(MidiPump)
        di.start()
        awaitinterrupt()
  finally:
        di.stop()

if '__main__' == __name__:
  main()
