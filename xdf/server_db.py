import re
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ServerDB:
    def __init__(self):
        self.maps = defaultdict(dict)

    @classmethod
    def parse(cls, data):
        inst = cls()
        time_re = re.compile(
            r'\\(?P<map_name>[\w-]+)/cts100record/time(?P<position>\d+)\\(?P<time>\d+)')
        speed_player_re = re.compile(
            r'\\(?P<map_name>[\w-]+)/cts100record/speed/crypto_idfp\\(?P<crypto_idfp>[a-zA-Z0-9_%]+)')
        speed_speed_re = re.compile(
            r'\\(?P<map_name>[\w-]+)/cts100record/speed/speed\\(?P<speed>[\d.]+)')
        record_re = re.compile(
            r'\\(?P<map_name>[\w-]+)/cts100record/crypto_idfp(?P<position>\d+)\\(?P<crypto_idfp>[a-zA-Z0-9_%]+)')
        for i in time_re.finditer(data):
            time = int(i.group('time'))
            inst.maps[i.group('map_name')]['speed'] = defaultdict(dict)
            if time > 0:
                inst.maps[i.group('map_name')][int(i.group('position'))] = {'time': time}
        for i in speed_player_re.finditer(data):
            if not i.group('map_name') in inst.maps:
                continue
            inst.maps[i.group('map_name')]['speed']['player'] = i.group('crypto_idfp')
        for i in speed_speed_re.finditer(data):
            if not i.group('map_name') in inst.maps:
                continue
            inst.maps[i.group('map_name')]['speed']['speed'] = i.group('speed')
        for i in record_re.finditer(data):
            pos = int(i.group('position'))
            if pos not in inst.maps[i.group('map_name')]:
                logger.warning('I have player id for position %s on %s but no time!', pos, i.group('map_name'))
                continue
            inst.maps[i.group('map_name')][pos]['player'] = i.group('crypto_idfp')
