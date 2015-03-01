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

import re, logging, os

log = logging.getLogger(__name__)

class Expression:

    def __init__(self, head, code, name):
        self.head = head
        self.code = code
        self.name = name

    def run(self, g):
        exec (self.head, g)
        exec (self.code, g)
        return g

    def __call__(self, view):
        return self.run({'config': view})[self.name]

    def modify(self, view, objname, obj):
        self.run({'config': view, objname: obj})

class Private:

    def __init__(self, expressions, rootcontext):
        self.expressions = expressions
        self.contextstack = [rootcontext]

    def withcontext(self, context, f):
        self.contextstack.append(context)
        try:
            return f()
        finally:
            self.contextstack.pop()

    def currentcontext(self):
        return self.contextstack[-1]

class View:

    def __init__(self, expressions):
        self.pRiVaTe = Private(expressions, self)

    def __getattr__(self, name):
        context = self.pRiVaTe.currentcontext()
        obj = self.pRiVaTe.expressions.expression(name)(context)
        for mod in self.pRiVaTe.expressions.modifiers(name):
            mod.modify(context, name, obj)
        return obj

class Fork:

    def __init__(self, parent):
        self.parent = parent

    def __getattr__(self, name):
        return self.parent.pRiVaTe.withcontext(self, lambda: getattr(self.parent, name))

class Expressions:

    # TODO LATER: Ideally inspect the AST as this can give false positives.
    toplevelassignment = re.compile(r'^([^\s]+)\s*=')

    @staticmethod
    def canonicalize(path):
        while True:
            try:
                link = os.readlink(path)
            except OSError:
                return path
            path = os.path.join(os.path.dirname(path), link)

    def __init__(self):
        self.expressions = {}

    def load(self, path):
        f = open(path)
        try:
            self.loadfile(path, f.readline)
        finally:
            f.close()

    def loadfile(self, path, readline):
        head = [
            "__file__ = %r\n" % self.canonicalize(path),
            'def sys_path_add(path):\n',
            '    import sys\n',
            '    if path not in sys.path:\n',
            '        sys.path.append(path)\n',
        ]
        line = readline()
        while line and self.toplevelassignment.search(line) is None:
            head.append(line)
            line = readline()
        tocode = lambda block: compile(block, '<string>', 'exec')
        log.debug("[%s] Header is first %s lines.", path, len(head))
        head = tocode(''.join(head))
        while line:
            m = self.toplevelassignment.search(line)
            if m is not None:
                name = m.group(1)
                self.expressions[name] = Expression(head, tocode(line), name)
            line = readline()

    def expression(self, name):
        return self.expressions[name]

    def modifiers(self, name):
        for e in self.expressions.itervalues():
            if e.name.startswith(name + '['):
                yield e
