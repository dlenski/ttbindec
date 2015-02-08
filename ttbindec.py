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

def read_header(buf, offset=0, tag2struct=defs.tag2struct):
    tag = ord(buf[offset])
    fh = defs.FILE_HEADER.from_buffer_copy(buf, offset+1)

    # sanity checks
    assert tag2struct[tag] == defs.FILE_HEADER
    assert fh.file_version == 7

    offset += 1 + ctypes.sizeof(defs.FILE_HEADER)
    rls = []
    for ii in range(fh.length_count):
        rl = defs.RECORD_LENGTH.from_buffer_copy(buf, offset)
        rls.append(rl)

        if rl.tag not in tag2struct:
            tag2struct[rl.tag] = ReprBytes("UNKNOWN_0x%02x"%rl.tag, rl.length-1)
        struct = tag2struct[rl.tag]

        # check that our expected size of this structure matches what the RECORD_LENGTH says
        assert ctypes.sizeof(struct)==rl.length - (struct is not defs.FILE_HEADER)
        offset += ctypes.sizeof(defs.RECORD_LENGTH)

    return tag, fh, rls, offset

def read_record(buf, offset, tag2struct=defs.tag2struct):
    tag = ord(buf[offset])
    struct = tag2struct[tag]
    assert struct != defs.FILE_HEADER
    record = struct.from_buffer_copy(buf, offset+1)
    offset += 1 + ctypes.sizeof(struct)
    return tag, record, offset

#####

if __name__=='__main__':
    p = argparse.ArgumentParser()
    p.add_argument('ttbin', nargs='*', type=argparse.FileType('rb'), default=sys.stdin)
    args = p.parse_args()

    for ttbin in args.ttbin:
        data = ttbin.read()

        tag, fh, rls, offset = read_header(data, 0)

        print "%08x %02x %s" % (0, tag, fh)
        for rl in rls:
            print "-------- %02x %s\t[ %s ]" % (rl.tag, rl, defs.tag2struct[rl.tag].__name__)

        while offset < len(data):
            tag, record, new_offset = read_record(data, offset)
            print "%08x %02x %s" % (offset, tag, record)
            offset = new_offset

        assert offset==len(data)
