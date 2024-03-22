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

class MissingAnnotationException(Exception): pass

class Special(object):

    @classmethod
    def gettypelabel(cls, type):
        # TODO: Dotted name can look misleading for nested classes.
        return type.__name__ if issubclass(type, cls) else "%s.%s" % (type.__module__, type.__name__)

class UnsatisfiableRequestException(Exception): pass

class ImpasseException(Exception): pass

unset = object()
