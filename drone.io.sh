#!/bin/bash

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

set -ex

condaversion=3.16.0

pwd

cd ..

hg clone https://bitbucket.org/combatopera/devutils

cd -

cd; pwd

wget http://repo.continuum.io/miniconda/Miniconda-$condaversion-Linux-x86_64.sh

bash Miniconda-$condaversion-Linux-x86_64.sh <<<$'\nyes\nminiconda\nno\n'

PATH="$PWD/miniconda/bin:$PATH"

cd -

conda install openssl=1.0.1h numpy cython pyflakes nose mock python=2.7.9=1

./tests
