#!/usr/bin/python
import struct, ctypes
from binascii import hexlify
import os, sys
import re
from collections import namedtuple, OrderedDict as odict

class StructReprMixin( ctypes.Structure ):
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, ', '.join('%s=%s' % (f[0], self._f_repr_(getattr(self,f[0]))) for f in self._fields_))
    def _f_repr_(self,f):
        if isinstance(f, ctypes.Array):
            if issubclass(f._type_, ctypes.c_char):
                return "(char[%d])%s" % (f._length_, repr(f.raw))
            elif ctypes.sizeof(f._type_)==1:
#                return "(%s[%d])%s" % (f._type_.__name__[2:], f._length_, hexlify(buffer(f)))
                return "(%s[%d])%s" % (f._type_.__name__[2:], f._length_, repr(str(buffer(f)).split('\x00')[0]))
            else:
                return "(%s[%d])%s" % (f._type_.__name__[2:], f._length_, repr(tuple(f[ii] for ii in range(f._length_))))
        else:
            return "(%s)%s" % (type(f).__name__, repr(f))

class StructPrettyReprMixin( StructReprMixin ):
    def __repr__(self):
        return "%s(\n  %s\n)" % (self.__class__.__name__, ',\n  '.join('%s=%s' % (f[0], self._f_repr_(getattr(self,f[0]))) for f in self._fields_))


#from SmartStruct import Struct

#####
# parse ttbin.h to find numeric constants
####

constants = dict()
tags = dict()
ttbin_h = open(os.path.join( os.path.dirname(__file__), 'ttbin.h' ))
for line in ttbin_h:
    line = line.strip()
    m = re.match( r"\#define \s+ (\w+) \s+ \( ((?:0x)?\w+) \) \s* ", line, re.X )
    if m:
        name, val = m.groups()
        constants[name] = int(val, 0)
        if name.startswith('TAG_'):
            tags[int(val,0)] = name[4:]

#####
# parse ttbin.c to find all the structure declarations
#####

Field = namedtuple("Field", "type name length comment")
c2p = dict(char='s',int8_t='b',uint8_t='B',int16_t='h',uint16_t='H',int32_t='i',uint32_t='I',float='f')

cstructs = dict()
pstructs = dict()
ttbin_c = open(os.path.join( os.path.dirname(__file__), 'ttbin.c' ))

in_struct = False
for line in ttbin_c:
    line = line.strip()
    if line == "typedef struct __attribute__((packed))":

        in_struct = True
        this_cstruct = []
#        this_pstruct = []

    elif in_struct:

        m = re.match( r"\} \s* (\w+) \s* ;", line, re.X)
        m2 = re.match( r"\s* (\w+) \s* (\w+) (?:\[(\d+)\])? \s* ; \s* (?: /\* \s*(.+?)\s* \*/ )?", line, re.X )
        if m:
            name = m.group(1)
            if name.startswith('FILE_') and name.endswith('_RECORD'):
                name = name[5:-7]

            fields = []
            for f in this_cstruct:
                t = getattr(ctypes, 'c_'+f.type[:-2] if f.type.endswith('_t') else 'c_'+f.type)
                if f.length is not None:
                    t = t*f.length
                fields.append((f.name, t))

            class Record(StructReprMixin, ctypes.LittleEndianStructure):
                _pack_ = 1;
                _fields_ = fields;
            Record.__name__ = name

            cstructs[name] = Record
#            pstructs[name] = Struct(name, this_pstruct, '<')
            in_struct = False
        elif m2:
            if m2.group(3) is None:
                length = None
            elif m2.group(3)=="0":
                continue # skip zero-length fields
            else:
                length=int(m2.group(3))
            this_cstruct.append( Field(type=m2.group(1), name=m2.group(2), length=length, comment=m2.group(4)) )
#            this_pstruct.append( (m2.group(2),(str(length) if length is not None else '')+c2p[m2.group(1)]) )

#import pprint
#pprint.pprint(constants)
#pprint.pprint(cstructs)
#pprint.pprint(pstructs)
#raise SystemExit

#####
# Read TTBIN file
#####

data = open(sys.argv[1], "rb").read()
offset = 0
reclen = {32:117,33:7,34:28,35:20,37:7,39:12,42:5,43:5,45:10,47:11,48:3,49:11,50:17,52:21,53:6,55:2,57:22,58:2,59:12,60:41,61:11,62:8,63:9} #v7 file format

while offset < len(data):
    tag = ord(data[offset])
    struct_name = tags.get(tag, 'UNKNOWN')
    print "Offset %d, tag %d, %s" % (offset, tag, struct_name)

    # sanity checking
    if offset==0:
        assert struct_name=='FILE_HEADER'
    elif struct_name == 'UNKNOWN':
        assert tag in reclen
    else:
        assert 1+ctypes.sizeof(cstructs[struct_name]) == reclen[tag]

    # display each record
    if struct_name=='UNKNOWN':
        print '  UNKNOWN(tag=%d, length=%d, data=%s)' % (tag, reclen[tag], hexlify(data[offset+1 : offset+reclen[tag]]))
        offset += reclen[tag]
    else:
        record = cstructs[struct_name].from_buffer_copy(data, offset+1)
        if struct_name=='FILE_HEADER':
            print ' ',record
            offset += 1 + ctypes.sizeof(cstructs['FILE_HEADER'])
            if record.file_version == 7:
                for ii in range(record.length_count):
                    rl = cstructs['RECORD_LENGTH'].from_buffer_copy(data, offset)
                    if rl.tag in tags:
                        print "    Tag %d for %s, length %d (@ offset %d)" % (rl.tag, tags[rl.tag], rl.length, offset)
                    else:
                        print "    Tag %d for UNKNOWN, length %d (@ offset %d)" % (rl.tag, rl.length, offset)
                    reclen[rl.tag] = rl.length
                    offset += ctypes.sizeof(cstructs['RECORD_LENGTH'])
            elif record.file_version == 5:
                offset -= 1
        else:
            print ' ',record
            offset += reclen[tag]

assert offset==len(data)
