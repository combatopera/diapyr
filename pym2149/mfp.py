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
from reg import Reg
from fractions import Fraction

prescalers = dict([1 + i, v] for i, v in enumerate([4, 10, 16, 50, 64, 100, 200]))
mfpclock = 2457600

class MFPTimer:

    def __init__(self):
        self.wavelength = Reg()
        self.wavelength.value = 2 # TODO LATER: Other shapes will have different numbers of steps.
        self.control = Reg()
        self.data = Reg()
        self.control.value = 0
        self.data.value = 0
        self.effect = Reg()
        self.effect.value = False
        self.control_data = Reg()
        self.control.link(lambda cd: cd[0], self.control_data)
        self.data.link(lambda cd: cd[1], self.control_data)
        self.freq = Reg()
        self.control_data.link(self.findtcrtdr, self.freq)

    def update(self, tcr, tdr):
        self.control_data.value = tcr, tdr
        self.effect.value = True

    def findtcrtdr(self, freq):
        diff = None
        for tcr, prescaler in prescalers.iteritems(): # XXX: Do we care about non-determinism?
            prescaler *= self.wavelength.value # Avoid having to multiply twice.
            tdr = int(round(mfpclock / (freq * prescaler)))
            if 1 <= tdr and tdr <= 255:
                rtp = tdr * prescaler
                d = abs(mfpclock / rtp - freq)
                if diff is None or d < diff:
                    tcrtdr = tcr, tdr
                    diff = d
        return tcrtdr

    def getnormperiod(self):
        return prescalers[self.control.value] * self.data.value * self.wavelength.value

    def getfreq(self): # Currently only called when effect is True.
        return mfpclock / self.getnormperiod()

    def getstepsize(self):
        tcr = self.control.value
        # TODO: Maybe something more logical than 0 for timer off.
        return Fraction(prescalers[tcr] * self.data.value if tcr in prescalers else 0, mfpclock)
