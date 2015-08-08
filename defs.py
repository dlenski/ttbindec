
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

#####
# Enumerations from ttbin.h
#####

class C_TAG(Enum):
    FILE_HEADER = 32
    STATUS = 33
    GPS = 34
    HEART_RATE = 37
    SUMMARY = 39
    POOL_SIZE = 42
    WHEEL_SIZE = 43
    TRAINING_SETUP = 45
    LAP = 47
    TREADMILL = 50
    SWIM = 52
    GOAL_PROGRESS = 53
    INTERVAL_SETUP = 57
    INTERVAL_START = 58
    INTERVAL_FINISH = 59
    RACE_SETUP = 60
    RACE_RESULT = 61
    ALTITUDE_UPDATE = 62
    HEART_RATE_RECOVERY = 63

class C_ACTIVITY(Enum):
    RUNNING = 0
    CYCLING = 1
    SWIMMING = 2
    STOPWATCH = 6
    TREADMILL = 7
    FREESTYLE = 8

class C_TRAINING(Enum):
    GOAL_DISTANCE = 0
    GOAL_TIME = 1
    GOAL_CALORIES = 2
    ZONES_PACE = 3
    ZONES_HEART = 4
    ZONES_CADENCE = 5
    RACE = 6
    LAPS_TIME = 7
    LAPS_DISTANCE = 8
    LAPS_MANUAL = 9
    STROKE_RATE = 10
    ZONES_SPEED = 11
    INTERVALS = 12

class C_OFFLINE(Enum):
    FORMAT_CSV = 1
    FORMAT_FIT = 2
    FORMAT_GPX = 4
    FORMAT_KML = 8
    FORMAT_PWX = 16
    FORMAT_TCX = 32
    FORMAT_COUNT = 6

#####
# In-file structures defined in ttbin.c
#####

class RECORD_LENGTH(StructReprMixin, LittleEndianStructure):
    _pack_ = 1
    _fields_ = (
        ('tag',c_uint8),
        ('length',c_uint16),
    )

class FILE_HEADER(StructReprMixin, LittleEndianStructure):
    _pack_ = 1
    _fields_ = (
        ('file_version',c_uint16),
        ('firmware_version',c_uint8*3),
        ('product_id',c_uint16),
        ('start_time',c_uint32), # local time
        ('software_version',c_uint8*16),
        ('gps_firmware_version',c_uint8*80),
        ('watch_time',c_uint32), # local time
        ('local_time_offset',c_int32), # seconds from UTC
        ('_reserved',c_uint8),
        ('length_count',c_uint8), # number of RECORD_LENGTH objects to follow
    )

class FILE_SUMMARY_RECORD(StructReprMixin, LittleEndianStructure):
    _pack_ = 1
    _fields_ = (
        ('activity',c_uint8),
        ('distance',c_float),
        ('duration',c_uint32), # seconds, after adding 1
        ('calories',c_uint16),
    )

class FILE_GPS_RECORD(StructReprMixin, LittleEndianStructure):
    _pack_ = 1
    _fields_ = (
        ('latitude',c_int32), # degrees * 1e7
        ('longitude',c_int32), # degrees * 1e7
        ('heading',c_uint16), # degrees * 100, N = 0, E = 9000
        ('gps_speed',c_uint16), # cm/s
        ('timestamp',c_uint32), # gps time (utc)
        ('calories',c_uint16),
        ('instant_speed',c_float), # m/s
        ('cum_distance',c_float), # metres
        ('cycles',c_uint8), # running = steps/sec, cycling = crank rpm
    )

class FILE_HEART_RATE_RECORD(StructReprMixin, LittleEndianStructure):
    _pack_ = 1
    _fields_ = (
        ('heart_rate',c_uint8), # bpm
        ('_reserved',c_uint8),
        ('timestamp',c_uint32), # local time
    )

class FILE_STATUS_RECORD(StructReprMixin, LittleEndianStructure):
    _pack_ = 1
    _fields_ = (
        ('status',c_uint8), # 0 = ready, 1 = active, 2 = paused, 3 = stopped
        ('activity',c_uint8), # 0 = running, 1 = cycling, 2 = swimming, 7 = treadmill, 8 = freestyle
        ('timestamp',c_uint32), # local time
    )

class FILE_TREADMILL_RECORD(StructReprMixin, LittleEndianStructure):
    _pack_ = 1
    _fields_ = (
        ('timestamp',c_uint32), # local time
        ('distance',c_float), # metres
        ('calories',c_uint16),
        ('steps',c_uint32),
        ('step_length',c_uint16), # cm, not implemented yet
    )

class FILE_SWIM_RECORD(StructReprMixin, LittleEndianStructure):
    _pack_ = 1
    _fields_ = (
        ('timestamp',c_uint32), # local time
        ('total_distance',c_float), # metres
        ('frequency',c_uint8),
        ('stroke_type',c_uint8),
        ('strokes',c_uint32), # since the last report
        ('completed_laps',c_uint32),
        ('total_calories',c_uint16),
    )

class FILE_LAP_RECORD(StructReprMixin, LittleEndianStructure):
    _pack_ = 1
    _fields_ = (
        ('total_time',c_uint32), # seconds since activity start
        ('total_distance',c_float), # metres
        ('total_calories',c_uint16),
    )

class FILE_RACE_SETUP_RECORD(StructReprMixin, LittleEndianStructure):
    _pack_ = 1
    _fields_ = (
        ('race_id',c_uint8*16), # only used for a web services race, 0 otherwise
        ('distance',c_float), # metres
        ('duration',c_uint32), # seconds
        ('name',c_char*16), # unused characters are zero
    )

class FILE_RACE_RESULT_RECORD(StructReprMixin, LittleEndianStructure):
    _pack_ = 1
    _fields_ = (
        ('duration',c_uint32), # seconds
        ('distance',c_float), # metres
        ('calories',c_uint16),
    )

class FILE_TRAINING_SETUP_RECORD(StructReprMixin, LittleEndianStructure):
    _pack_ = 1
    _fields_ = (
        ('type',c_uint8), # 0 = goal distance, 1 = goal time, 2 = goal calories, 3 = zones pace, 4 = zones heart, 5 = zones cadence, 6 = race, 7 = laps time, 8 = laps distance, 9 = laps manual, 10 = stroke rate, 11 = zones speed, 12 = intervals
        ('min',c_float), # metres, seconds, calories, secs/km, km/h, bpm
        ('max',c_float), # secs/km, km/h, bpm (only used for zones)
    )

class FILE_GOAL_PROGRESS_RECORD(StructReprMixin, LittleEndianStructure):
    _pack_ = 1
    _fields_ = (
        ('percent',c_uint8), # 0 - 100
        ('value',c_uint32), # metres, seconds, calories
    )

class FILE_INTERVAL_SETUP_RECORD(StructReprMixin, LittleEndianStructure):
    _pack_ = 1
    _fields_ = (
        ('warm_type',c_uint8), # 0 = distance, 1 = time
        ('warm',c_uint32), # metres, seconds
        ('work_type',c_uint8), # 0 = distance, 1 = time
        ('work',c_uint32), # metres, seconds
        ('rest_type',c_uint8), # 0 = distance, 1 = time
        ('rest',c_uint32), # metres, seconds
        ('cool_type',c_uint8), # 0 = distance, 1 = time
        ('cool',c_uint32), # metres, seconds
        ('sets',c_uint8),
    )

class FILE_INTERVAL_START_RECORD(StructReprMixin, LittleEndianStructure):
    _pack_ = 1
    _fields_ = (
        ('type',c_uint8), # 1 = warmup, 2 = work, 3 = rest, 4 = cooldown, 5 = finished
    )

class FILE_INTERVAL_FINISH_RECORD(StructReprMixin, LittleEndianStructure):
    _pack_ = 1
    _fields_ = (
        ('type',c_uint8), # 1 = warmup, 2 = work, 3 = rest, 4 = cooldown
        ('total_time',c_uint32), # seconds
        ('total_distance',c_float), # metres
        ('total_calories',c_uint16),
    )

class FILE_HEART_RATE_RECOVERY_RECORD(StructReprMixin, LittleEndianStructure):
    _pack_ = 1
    _fields_ = (
        ('status',c_uint32), # 3 = good, 4 = excellent
        ('heart_rate',c_uint32), # bpm
    )

class FILE_ALTITUDE_RECORD(StructReprMixin, LittleEndianStructure):
    _pack_ = 1
    _fields_ = (
        ('rel_altitude',c_int16), # altitude change from workout start
        ('total_climb',c_float), # metres, descents are ignored
        ('qualifier',c_uint8), # not defined yet
    )

class FILE_POOL_SIZE_RECORD(StructReprMixin, LittleEndianStructure):
    _pack_ = 1
    _fields_ = (
        ('pool_size',c_int32), # centimeters
    )

class FILE_WHEEL_SIZE_RECORD(StructReprMixin, LittleEndianStructure):
    _pack_ = 1
    _fields_ = (
        ('wheel_size',c_uint32), # millimetres
    )

class FILE_INVALID(StructReprMixin, LittleEndianStructure):
    _pack_ = 1
    _fields_ = ()

#####
# Tag to structure map
#####

tag2struct = {
    -1: RECORD_LENGTH,
    32: FILE_HEADER,
    39: FILE_SUMMARY_RECORD,
    34: FILE_GPS_RECORD,
    37: FILE_HEART_RATE_RECORD,
    33: FILE_STATUS_RECORD,
    50: FILE_TREADMILL_RECORD,
    52: FILE_SWIM_RECORD,
    47: FILE_LAP_RECORD,
    60: FILE_RACE_SETUP_RECORD,
    61: FILE_RACE_RESULT_RECORD,
    45: FILE_TRAINING_SETUP_RECORD,
    53: FILE_GOAL_PROGRESS_RECORD,
    57: FILE_INTERVAL_SETUP_RECORD,
    58: FILE_INTERVAL_START_RECORD,
    59: FILE_INTERVAL_FINISH_RECORD,
    63: FILE_HEART_RATE_RECOVERY_RECORD,
    62: FILE_ALTITUDE_RECORD,
    42: FILE_POOL_SIZE_RECORD,
    43: FILE_WHEEL_SIZE_RECORD,
}
