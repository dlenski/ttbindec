#!/usr/bin/python
from __future__ import division
import argparse
import datetime, sys, os
import urllib2, json

import ttbindec, defs

p = argparse.ArgumentParser()
p.add_argument('ttbin', nargs='*', type=argparse.FileType('rb'), default=sys.stdin, help='.ttbin files (default stdin)')
p.add_argument('-g', '--geolocate', action='store_true', help='Geolocate using Google Maps api')
p.add_argument('-r', '--rename', action='store_true', help='Rename files to YYYY-MM-DDTHH:MM:SS_Activity_Duration.ttbin')
args = p.parse_args()

for ttbin in args.ttbin:
    if len(args.ttbin)>1:
        indent="    "
        print "\n%s:" % ttbin.name
    else:
        indent=""

    data = ttbin.read()
    tag, fh, rls, offset = ttbindec.read_header(data)

    fw = '%d.%d.%d' % tuple(fh.firmware_version)
    product = "%d (%s)" % (fh.product_id, {1001:"Runner",1002:"MultiSport"}.get(fh.product_id,"Unknown"))
    start_time = datetime.datetime.fromtimestamp(fh.start_time-fh.local_time_offset)

    activity, laps, distance, duration, end_time = 'UNKNOWN', 1, None, 'UNKNOWN', None
    fp = None
    while offset<len(data):
        tag, rec, offset = ttbindec.read_record(data, offset)
        if isinstance(rec, defs.FILE_STATUS_RECORD):
            try:
                activity = defs.C_ACTIVITY(rec.activity).name.title()
            except ValueError:
                activity = None
            end_time = datetime.datetime.fromtimestamp(rec.timestamp-fh.local_time_offset)
        elif isinstance(rec, defs.FILE_LAP_RECORD):
            laps += 1
        elif isinstance(rec, defs.FILE_SUMMARY_RECORD):
            distance = rec.distance
            duration = "%02d:%02d:%02d" % (rec.duration//3600, (rec.duration//60)%60, rec.duration%60)
        elif fp is None and isinstance(rec, defs.FILE_GPS_RECORD):
            lat, long = "%08.d"%rec.latitude, "%08.d"%rec.longitude
            fp = "%s.%s,%s.%s" % (lat[:-7],lat[-7:],long[:-7],long[-7:])

    print indent+"Device: %s, firmware v%s" % (product, fw)
    print indent+"Activity: %s" % activity
    print indent+"Start time: %s" % start_time.isoformat()
    print indent+"End time: %s" % end_time.isoformat()
    print indent+"Duration: %s" % duration
    if fp:
        print indent+"Start location: %s" % fp
        if args.geolocate:
            try:
                j = json.load(urllib2.urlopen("http://maps.googleapis.com/maps/api/geocode/json?latlng=%s" % fp))
                addr = j['results'][0]['formatted_address']
                print indent+"    %s" % addr
            except Exception:
                pass
    if distance:
        print indent+"Distance: %gm, %d laps" % (distance, laps)

    if args.rename and ttbin is not sys.stdin:
        ttbin.close()
        newfn = '%s_%s_%s.ttbin' % (start_time.isoformat(), activity, duration)
        newpath = os.path.join(os.path.dirname(ttbin.name), newfn)
        if os.path.exists(newpath):
            if not os.path.samefile(ttbin.name, newpath):
                print>>sys.stderr, "File exists, not renaming: %s" % newpath
        else:
            os.rename(ttbin.name, newpath)
            print indent+"Renamed to %s" % newfn
