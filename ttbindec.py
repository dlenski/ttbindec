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
    if tag in tag2struct and tag!=32 and offset+1+ctypes.sizeof(tag2struct[tag])<=len(buf):
        struct = tag2struct[tag]
        assert struct != defs.FILE_HEADER
        record = struct.from_buffer_copy(buf, offset+1)
        offset += 1 + ctypes.sizeof(struct)
        return tag, record, offset
    else:
        junkstart, junkend = offset, None
        while offset<len(buf):
            tag1, tag2 = ord(buf[offset]), None
            if tag1 in tag2struct and tag1!=32 and offset+1+ctypes.sizeof(tag2struct[tag1])<=len(buf):
                #print>>sys.stderr, "tag1 0x%02x at offset 0x%04x" % (tag1, offset)
                struct1 = tag2struct[tag1]
                tag2 = ord(buf[offset+1+ctypes.sizeof(struct1)])
                if tag2 in tag2struct and tag2!=32:
                    junkend = offset
            if junkend is not None:
                tag, struct = tag1, struct1
                #print>>sys.stderr, "Tag 0x%02x at offset 0x%04x, preceded by junk: %s" % (tag, offset, hexlify(buf[junkstart:junkend]))
                #print "Tag 0x%02x at offset 0x%04x, preceded by junk: %s" % (tag, offset, hexlify(buf[junkstart:junkend]))
                break
            offset += 1
        else:
            junkend = len(buf)
            #print>>sys.stderr, "File ends with junk: %s" % (hexlify(buf[junkstart:junkend]))

        struct = ReprBytes("SUSPECTED_JUNK", junkend-junkstart)
        record = struct.from_buffer_copy(buf, junkstart)
        return None, record, offset

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
            print "%08x %s %s" % (offset, '__' if tag is None else ("%02x"%tag), record)
            offset = new_offset

        assert offset==len(data)
