import re
from collections import defaultdict
import logging
from urllib.parse import unquote

from django.conf import settings

from xanmel.modules.xonotic.models import *

logger = logging.getLogger(__name__)


class ServerDB:
    def __init__(self):
        self.maps = defaultdict(dict)
        self.uid_to_name = dict()

    @classmethod
    def parse_server(cls, server_id):
        path = settings.XONOTIC_XDF_DATABASES[server_id]
        with open(path, 'r') as f:
            return cls.parse(f.read())

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
        uid_to_name_re = re.compile(
            r'\\/uid2name/(?P<crypto_idfp>[\w+/=]+)\\(?P<nickname>.*)'
        )
        for i in time_re.finditer(data):
            time = int(i.group('time'))
            inst.maps[i.group('map_name')]['speed'] = defaultdict(dict)
            if time > 0:
                inst.maps[i.group('map_name')][int(i.group('position'))] = {'time': time}
        for i in speed_player_re.finditer(data):
            if not i.group('map_name') in inst.maps:
                continue
            inst.maps[i.group('map_name')]['speed']['player'] = unquote(i.group('crypto_idfp'))
        for i in speed_speed_re.finditer(data):
            if not i.group('map_name') in inst.maps:
                continue
            inst.maps[i.group('map_name')]['speed']['speed'] = float(i.group('speed'))
        for i in record_re.finditer(data):
            pos = int(i.group('position'))
            if pos not in inst.maps[i.group('map_name')]:
                logger.warning('I have player id for position %s on %s but no time!', pos, i.group('map_name'))
                continue
            inst.maps[i.group('map_name')][pos]['player'] = unquote(i.group('crypto_idfp'))
        for i in uid_to_name_re.finditer(data):
            inst.uid_to_name[i.group('crypto_idfp')] = unquote(i.group('nickname'))
        return inst

    def save(self, server_id):
        server = Server.get(id=server_id)
        for map_name, item in self.maps.items():
            map, _ = Map.get_or_create(server=server, name=map_name)
            positions = []
            for k, v in item.items():
                player = Player.from_cryptoidfp(v['player'], settings.XONOTIC_ELO_REQUEST_SIGNATURE)
                if player is None:
                    raw_nickname = self.uid_to_name.get(v['player'], 'Unregistered player')
                    player = Player.create(crypto_idfp=v['player'], raw_nickname=raw_nickname,
                                           nickname=Color.dp_to_none(raw_nickname.encode('utf8')).decode('utf8'))
                if k == 'speed':
                    try:
                        record = XDFSpeedRecord.get(XDFSpeedRecord.map == map)
                    except DoesNotExist:
                        XDFSpeedRecord.create(map=map, player=player, speed=v['speed'])
                    else:
                        if record.player != player or record.speed < v['speed']:
                            logger.info('%s: speed record by %s', map.name, player.nickname)
                            record.player = player
                            record.speed = v['speed']
                            record.timestamp = current_time()
                            record.save()
                else:
                    positions.append((player, k, v['time']))
            positions.sort(key=lambda x: x[1])
            old_positions = dict([(i.player.crypto_idfp, (i.position, i.time))
                                  for i in XDFTimeRecord.select().where(XDFTimeRecord.map == map)])
            for position in positions:
                try:
                    old_pos = XDFTimeRecord.get(XDFTimeRecord.map == map, XDFTimeRecord.position == position[1])
                except DoesNotExist:
                    XDFTimeRecord.create(map=map, position=position[1], player=position[0], time=position[2])
                else:
                    if old_pos.player == position[0]:
                        if old_pos.time == position[2]:
                            # Nothing has changed
                            pass
                        elif old_pos.time > position[2]:
                            logger.info('%s: player %s improved time ', map.name, position[0].nickname)
                            old_pos.time = position[2]
                            old_pos.timestamp = current_time()
                            old_pos.save()
                        else:
                            # same position, worse time, this should never happen!
                            logger.warning('%s: for player %s degraded!', map.name, position[0].nickname)
                            old_pos.time = position[2]
                            old_pos.save()
                    else:
                        old_player_position = old_positions.get(position[0].crypto_idfp)
                        if old_player_position is None:
                            logger.info('%s: player %s is now %s', map.name, position[0].nickname, position[1])
                            old_pos.player = position[0]
                            old_pos.time = position[2]
                            old_pos.timestamp = current_time()
                            old_pos.save()
                        else:
                            if old_player_position[0] > position[1]:
                                logger.info('%s: player %s improved his position from %s to %s', map.name,
                                            position[0].nickname, old_player_position[0], position[1])
                                old_pos.player = position[0]
                                old_pos.time = position[2]
                                old_pos.timestamp = current_time()
                                old_pos.save()
                            else:
                                logger.info('%s: player %s kicked from %s to %s', map.name,
                                            position[0].nickname, old_player_position[0], position[1])
                                old_pos.player = position[0]
                                old_pos.time = position[2]
                                old_pos.save()
