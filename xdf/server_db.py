import re
from collections import defaultdict
import logging
from decimal import Decimal
from urllib.parse import unquote

import requests
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
        if path.startswith('http'):
            data = requests.get(path).text
        else:
            with open(path, 'r') as f:
                data = f.read()
        return cls.parse(data)

    @classmethod
    def parse(cls, data):
        inst = cls()
        cls.db = XonoticDB(data)
        time_re = re.compile('(.*)/cts100record/time(\d+)')
        position_re = re.compile('(.*)/cts100record/crypto_idfp(\d+)')
        speed_id_re = re.compile('(.*)/cts100record/speed/crypto_idfp')
        speed_value_re = re.compile('(.*)/cts100record/speed/speed')
        for k, v in cls.db.filter(time_re, is_regex=True):
            time = int(v)
            match = time_re.match(k)
            map_name = match.group(1)
            position = int(match.group(2))
            inst.maps[map_name]['speed'] = defaultdict(dict)
            if time > 0:
                inst.maps[map_name][position] = {'time': Decimal(time) / 100}
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
            if not (re.match(r'\d+\.\d+', v) or re.match(r'\d+', v)):
                print(map_name, v)
                v = '0'
            inst.maps[map_name]['speed']['speed'] = Decimal(v)
        for k, v in cls.db.filter(position_re, is_regex=True):
            match = position_re.match(k)
            map_name = match.group(1)
            pos = int(match.group(2))
            if pos not in inst.maps[map_name]:
                logger.warning('I have player id for position %s on %s but no time!', pos, map_name)
                continue
            inst.maps[map_name][pos]['player'] = v
        return inst

    def save(self, server_id):
        server = XDFServer.get(id=server_id)
        prev_speed_records = {}
        for i in XDFSpeedRecord.select().where(XDFSpeedRecord.server == server):
            prev_speed_records[i.map] = i
        changed_maps = set()
        prev_time_records = XDFTimeRecord.get_records_for(server)
        for map_name, item in self.maps.items():
            positions = {}
            max_pos = 0

            for k, v in item.items():
                if not v.get('player'):
                    # Why?
                    print(k, v)
                    continue
                player = XDFPlayer.get_player(v['player'], self.uid_to_name(v['player']),
                                              settings.XONOTIC_ELO_REQUEST_SIGNATURE)
                if k == 'speed':
                    create_news = False
                    if map_name in prev_speed_records:
                        record = prev_speed_records[map_name]
                        if record.speed < v['speed']:
                            logger.info('%s: speed record by %s', map_name, player.nickname)
                            record.player = player
                            record.speed = v['speed']
                            record.timestamp = current_time()
                            record.save()
                            create_news = True
                    else:
                        record = XDFSpeedRecord.create(map=map_name, server=server, player=player, speed=v['speed'])
                        create_news = True

                    if create_news:
                        XDFNewsFeed.create(event_type=EventType.SPEED_RECORD.value,
                                           speed_record=record)
                else:
                    positions[k] = v
                    if k > max_pos:
                        max_pos = k
            cur_shift = 0
            for pos in range(1, max_pos + 1):
                if pos not in positions:
                    print('No position {} on map {}'.format(pos, map_name))
                    max_pos -= 1
                    cur_shift += 1
                    continue
                player = XDFPlayer.get_player(positions[pos]['player'], self.uid_to_name(positions[pos]['player']),
                                              settings.XONOTIC_ELO_REQUEST_SIGNATURE)
                time = positions[pos]['time']
                prev_position = prev_time_records[map_name].get(player.id)
                real_pos = pos - cur_shift
                create_news = False
                if prev_position:
                    if prev_position.time > time:
                        # Time improvement
                        create_news = True
                        prev_position.timestamp = current_time()
                        changed_maps.add(map_name)
                    elif prev_position.time == time and prev_position.server_pos == real_pos:
                        # Same record
                        continue
                    elif prev_position.time == time and prev_position.server_pos != real_pos:
                        # position changed without time change
                        changed_maps.add(map_name)
                    elif prev_position.time < time:
                        # duplicate
                        max_pos -= 1
                        cur_shift += 1
                        continue
                    prev_position.time = time
                    prev_position.server_pos = real_pos
                    prev_position.save()
                    record = prev_position
                else:
                    # New time record
                    create_news = True
                    changed_maps.add(map_name)
                    record = XDFTimeRecord.create(map=map_name, server=server, player=player, server_pos=real_pos,
                                                  time=time)
                if create_news:
                    XDFNewsFeed.create(event_type=EventType.TIME_RECORD.value,
                                       time_record=record)
            for i in XDFTimeRecord.select().where(XDFTimeRecord.server == server,
                                                  XDFTimeRecord.map == map_name,
                                                  XDFTimeRecord.server_pos > max_pos):
                i.delete_instance(recursive=True)
            XDFTimeRecord.update(server_max_pos=max_pos).where(XDFTimeRecord.server == server,
                                                               XDFTimeRecord.map == map_name).execute()
        return changed_maps

    def pull_video(self, server_id):
        url = settings.XONOTIC_XDF_VIDEO_DATABASES.get(server_id)
        if url is None:
            return
        server = XDFServer.get(id=server_id)
        data = requests.get(url).text
        for line in data.split('\n'):
            if line:
                map_name, time, youtube_id, nickname = line.split(' - ', 4)
                if time.count('.') == 1:
                    time = Decimal(time)
                elif time.count('.') == 2:
                    mins, seconds = time.split('.', 1)
                    time = Decimal(mins) * 60 + Decimal(seconds)
                else:
                    print('WRONG VIDEO TIME', time)
                    continue
                try:
                    record = XDFTimeRecord.get(XDFTimeRecord.map == map_name,
                                               XDFTimeRecord.server == server,
                                               XDFTimeRecord.time == Decimal(time))
                except DoesNotExist:
                    print('WARNING: existing youtube vid for non-existent record', map_name, time, youtube_id)
                    continue
                video_url = 'https://youtu.be/{}'.format(youtube_id)
                if record.video_url == video_url:
                    continue
                XDFTimeRecord.update(video_url=None).where(
                    XDFTimeRecord.map == map_name,
                    XDFTimeRecord.server == server).execute()
                record.video_url = video_url
                record.save()
