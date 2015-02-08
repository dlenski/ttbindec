#!/usr/bin/python
import defs, ctypes
from binascii import hexlify
import argparse
import os, sys
import re
from collections import namedtuple, OrderedDict as odict

def ReprBytes(name, length):
    t = ctypes.c_char*length
    t.__name__ = name
    t.__repr__ = lambda self: "%s(unhexlify('%s'))"%(name, hexlify(self.raw))
    return t

p = argparse.ArgumentParser()
p.add_argument('ttbin', nargs='*', type=argparse.FileType('rb'), default=sys.stdin)

data = open(sys.argv[1], "rb").read()
offset = 0

tag = ord(data[offset])
assert defs.tag2struct[tag] == defs.FILE_HEADER
fh = defs.FILE_HEADER.from_buffer_copy(data, offset+1)
assert fh.file_version == 7
print "%08x %02x %s" % (offset, tag, fh)
offset += 1 + ctypes.sizeof(defs.FILE_HEADER)
for ii in range(fh.length_count):
    rl = defs.RECORD_LENGTH.from_buffer_copy(data, offset)
    if rl.tag not in defs.tag2struct:
        defs.tag2struct[rl.tag] = ReprBytes("UNKNOWN_0x%02x"%rl.tag, rl.length-1)
    struct = defs.tag2struct[rl.tag]

    assert ctypes.sizeof(struct)==rl.length - (struct is not defs.FILE_HEADER)
    print "%08x %02x %s\t[ %s ]" % (offset, rl.tag, rl, struct.__name__)
    offset += ctypes.sizeof(defs.RECORD_LENGTH)

while offset < len(data):
    tag = ord(data[offset])
    struct = defs.tag2struct.get(tag)
    # sanity checking
    assert struct.__name__!='FILE_HEADER'

    # display each record
    record = struct.from_buffer_copy(data, offset+1)
    print "%08x %02x %s" % (offset, tag, record)
    offset += ctypes.sizeof(struct)+1

assert offset==len(data)
