import re
from collections import defaultdict
import logging
from urllib.parse import unquote

from django.conf import settings

from xon_db import XonoticDB
from xanmel.modules.xonotic.models import *

logger = logging.getLogger(__name__)


class ServerDB:
    def __init__(self):
        self.maps = defaultdict(dict)

    def uid_to_name(self, crypto_idfp):
        return self.db.get('/uid2name/' + crypto_idfp, 'Unregistered player')

    @classmethod
    def parse_server(cls, server_id):
        path = settings.XONOTIC_XDF_DATABASES[server_id]
        with open(path, 'r') as f:
            return cls.parse(f.read())

    @classmethod
    def parse(cls, data):
        inst = cls()
        cls.db = XonoticDB(data)
        time_re = re.compile('(.*)/cts100record/time(\d+)')
        position_re = re.compile('(.*)/cts100record/crypto_idfp(\d+)')
        speed_id_re = re.compile('(.*)/cts100record/speed/crypto_idfp')
        speed_value_re = re.compile('(.*)/cts100record/speed/speed')
        for k, time in cls.db.filter(time_re, is_regex=True):
            match = time_re.match(k)
            map_name = match.group(1)
            position = int(match.group(2))
            inst.maps[map_name]['speed'] = defaultdict(dict)
            if time > 0:
                inst.maps[map_name][position] = {'time': time}
        for k, crypto_idfp in cls.db.filter(speed_id_re, is_regex=True):
            match = speed_id_re.match(k)
            map_name = match.group(1)
            if map_name not in inst.maps:
                continue
            inst.maps[map_name]['speed']['player'] = crypto_idfp
        for k, v in cls.db.filter(speed_value_re, is_regex=True):
            match = speed_value_re.match(k)
            map_name = match.group(1)
            if map_name not in inst.maps:
                continue
            inst.maps[map_name]['speed']['speed'] = float(v)
        for k, v in cls.db.filter(position_re):
            match = position_re.match(k)
            map_name = match.group(1)
            pos = int(match.group(2))
            if pos not in inst.maps[map_name]:
                logger.warning('I have player id for position %s on %s but no time!', pos, map_name)
                continue
            inst.maps[map_name][pos]['player'] = v
        return inst

    def save(self, server_id):
        server = Server.get(id=server_id)
        for map_name, item in self.maps.items():
            map, _ = Map.get_or_create(server=server, name=map_name)
            positions = []
            for k, v in item.items():
                player = Player.from_cryptoidfp(v['player'], settings.XONOTIC_ELO_REQUEST_SIGNATURE)
                if player is None:
                    raw_nickname = self.uid_to_name(v['player'])
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
