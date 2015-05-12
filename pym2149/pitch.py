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
from util import singleton
import math

class Pitch(float):

    a4freq = 440
    a4midi = 69
    names = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')

    def freq(self):
        return Freq(self.a4freq * (2 ** ((self - self.a4midi) / 12)))

    def __add__(self, that):
        return self.__class__(float.__add__(self, that))

    def __sub__(self, that):
        return self.__class__(float.__sub__(self, that))

    def __str__(self):
        nearest = int(math.ceil(self - .5))
        octave = nearest // 12
        note = nearest % 12
        cents = int(round((self - nearest) * 100))
        octave -= 1
        notestr = self.names[note]
        if len(notestr) < 2:
            notestr += '.'
        octavestr = str(octave)
        if len(octavestr) < 2:
            octavestr = '.' + octavestr
        if abs(cents) < 10:
            centsstr = ' ' * 3
        else:
            centsstr = "%+d" % cents
        return notestr + octavestr + centsstr

@singleton
class shapescale:

    trishapes = frozenset([0xa, 0xe])

    def __call__(self, shape):
        # Musically, the triangular shapes have twice the scale:
        return (256, 512)[shape in self.trishapes]

class Freq(float):

    def periodimpl(self, clock, scale):
        return Period(round(clock / (scale * self)))

    def toneperiod(self, clock):
        return self.periodimpl(clock, 16)

    def noiseperiod(self, clock):
        return self.periodimpl(clock, 16) # First notch at freq.

    def envperiod(self, clock, shape):
        return self.periodimpl(clock, shapescale(shape))

    def pitch(self):
        return Pitch(Pitch.a4midi + 12 * math.log(self / Pitch.a4freq, 2))

    def __mul__(self, that):
        return self.__class__(float.__mul__(self, that))

class Period(int):

    def tonefreq(self, clock):
        return Freq(clock / (16 * self))

    def envfreq(self, clock, shape):
        return Freq(clock / (shapescale(shape) * self))
