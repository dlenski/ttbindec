#!/usr/bin/python
import os, sys
import re
import itertools
import argparse
from collections import namedtuple, OrderedDict as odict

Field = namedtuple("Field", "type name length comment")

p = argparse.ArgumentParser()
p.add_argument('ttbindir', default='.', nargs='?')
p.add_argument('-o', '--output', type=argparse.FileType('wt'), default=open('defs.py','wt'))
args = p.parse_args()
o = args.output

print>>o, """
from ctypes import *
from enum import Enum

class StructReprMixin( Structure ):
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, ', '.join('%s=%s' % (f[0], self._f_repr_(getattr(self,f[0]))) for f in self._fields_))
    def _f_repr_(self,f):
        if isinstance(f, Array):
            if issubclass(f._type_, c_char):
                return repr(f.raw)
            else:
                return tuple(f[ii] for ii in range(f._length_))
        else:
            return f
    def _ft_repr_(self,f):
        if isinstance(f, Array):
            if issubclass(f._type_, c_char):
                return "(char[%d])%s" % (f._length_, repr(f.raw))
            else:
                return "(%s[%d])%s" % (f._type_.__name__[2:], f._length_, repr(tuple(f[ii] for ii in range(f._length_))))
        else:
            return "(%s)%s" % (type(f).__name__, repr(f))
"""

#####
# parse ttbin.h to find numeric constants
####

print>>o, "#####\n# Enumerations from ttbin.h\n#####\n"

constants = []
ttbin_h = open(os.path.join(args.ttbindir, 'ttbin.h'))
for line in ttbin_h:
    line = line.strip()
    m = re.match( r"\#define \s+ (\w+) \s+ \( ((?:0x)?\w+) \) \s* ", line, re.X )
    if m:
        name, val = m.groups()
        constants.append((name, int(val, 0)))

tag2name, name2tag = odict(), odict()
for enum, group in itertools.groupby(constants, lambda (k,v): k.split('_')[0]):
    print>>o, 'class C_%s(Enum):' % enum
    for k,v in group:
        valname = k[len(enum)+1:]
        print>>o, '    %s = %d' % (valname, v)
        if enum=='TAG':
            name2tag[valname] = v
    print>>o

#####
# parse ttbin.c to find all the structure declarations
#####

print>>o, "#####\n# In-file structures defined in ttbin.c\n#####\n"

cstructs = []
ttbin_c = open(os.path.join(args.ttbindir, 'ttbin.c'))
in_struct = False
for line in ttbin_c:
    line = line.strip()
    while '/*' in line and '*/' not in line: # comment concatenater Uber-kludge
        line += ' '+ttbin_c.next().strip()

    if re.match(r"typedef \s+ struct \s+  __attribute__ \s* \(\( \s* packed \s* \)\)", line, re.X):

        in_struct = True
        this_cstruct = []

    elif in_struct:

        m_end = re.match( r"\} \s* (\w+) \s* ;", line, re.X)
        m_field = re.match( r"\s* (\w+) \s* (\w+) (?:\[(\d+)\])? \s* ; \s* (?: /\* \s*(.+?)\s* \*/ )?", line, re.X|re.M )

        if m_end:
            name = m_end.group(1)

            name2 = name[5:-7] if name.startswith('FILE_') and name.endswith('_RECORD') else name
            for tn, tag in name2tag.iteritems():
                if name2 in tn and tag not in tag2name:
                    tag2name[tag] = name
                    break
            else:
                tag2name[min(tag2name.keys()+[-1])] = name

            print>>o, "class %s(StructReprMixin, LittleEndianStructure):" % name
            print>>o, "    _pack_ = 1"
            print>>o, "    _fields_ = ("
            for f in this_cstruct:
                ct = 'c_'+(f.type[:-2] if f.type.endswith('_t') else f.type)
                if f.length is not None:
                    ct += '*%d'%f.length
                print>>o, "        ('%s',%s),%s" % (f.name, ct, " # "+f.comment if f.comment else '')
            print>>o, "    )"
            print>>o

            in_struct = False
        elif m_field:
            m = m_field
            if m.group(3) is None:
                length = None
            elif m.group(3)=="0":
                continue # skip zero-length fields
            else:
                length=int(m.group(3))
            this_cstruct.append( Field(type=m.group(1), name=m.group(2), length=length, comment=m.group(4)) )

#####
# Output map from tags to structures
#####

print>>o, "#####\n# Tag to structure map\n#####\n"

print>>o, "tag2struct = {"
for tn in tag2name.iteritems():
    print>>o, "    %d: %s," % tn
print>>o, "}"

print "Wrote definitions to %s." % o.name
