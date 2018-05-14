import urllib.parse

from django.http import Http404
from django.shortcuts import render
from django.conf import settings
from django.views import View
from peewee import fn

from xanmel.modules.xonotic.models import *
from xdf.templatetags.xdf import format_time

from .forms import NewsFeedFilterForm, MapListFilterForm, MapFilterForm
from .utils import paginate_query


def format_player_with_link(player):
    return '<a href="#">{}</a>'.format(player.nickname)


class IndexView(View):
    @staticmethod
    def format_news_item(news_item):
        if news_item.event_type == EventType.SPEED_RECORD.value:
            return "{} set high speed record &mdash; {}qu/s".format(
                format_player_with_link(news_item.speed_record.player),
                round(news_item.speed_record.speed)
            )
        elif news_item.event_type == EventType.TIME_RECORD.value:
            if news_item.time_record.video_url:
                yt_link = '<a target="_blank" href="{}">{}s <i class="fab fa-youtube"></i></a>'.format(
                    news_item.time_record.video_url,
                    format_time(news_item.time_record.time),
                )
            else:
                yt_link = '{}s'.format(format_time(news_item.time_record.time),)
            return "{} set time &mdash; {} (server {}/{}, global {}/{})".format(
                format_player_with_link(news_item.time_record.player),
                yt_link,
                news_item.time_record.server_pos,
                news_item.time_record.server_max_pos,
                news_item.time_record.global_pos,
                news_item.time_record.global_max_pos,
            )

    def get(self, request):
        form = NewsFeedFilterForm(data=request.GET)
        if not form.is_valid():
            raise Http404
        p1 = XDFPlayer.alias()
        p2 = XDFPlayer.alias()
        news = (XDFNewsFeed.select()
                .join(XDFTimeRecord, JOIN_LEFT_OUTER, on=(XDFNewsFeed.time_record == XDFTimeRecord.id))
                .join(p1, JOIN_LEFT_OUTER, on=(XDFTimeRecord.player == p1.id))
                .join(XDFSpeedRecord, JOIN_LEFT_OUTER, on=(XDFNewsFeed.speed_record == XDFSpeedRecord.id))
                .join(p2, JOIN_LEFT_OUTER, on=(XDFSpeedRecord.player == p2.id))
                .order_by(XDFNewsFeed.timestamp.desc()))
        if form.cleaned_data['maps']:
            pattern = '%{}%'.format(form.cleaned_data['maps'])
            news = news.where(XDFTimeRecord.map ** pattern | XDFSpeedRecord.map ** pattern)
        if form.cleaned_data['players']:
            pattern = '%{}%'.format(form.cleaned_data['players'])
            news = news.where(p1.nickname ** pattern | p2.nickname ** pattern)
        servers = form.cleaned_data['servers']
        news = news.where(XDFTimeRecord.server.in_(servers) | XDFSpeedRecord.server.in_(servers))
        news = news.where(XDFNewsFeed.event_type.in_(form.cleaned_data['event_types']))
        if form.cleaned_data['position_lte']:
            news = news.where(XDFTimeRecord.server_pos <= form.cleaned_data['position_lte'])
        total_news = news.count()
        news = paginate_query(request, news)
        return render(request, 'xdf/index.jinja', {
            'form': form,
            'news': news,
            'total_news': total_news,
            'format_news_item': self.format_news_item,
            'current_nav_tab': 'index'
        })


class ServerListView(View):
    @staticmethod
    def count_maps(server):
        return XDFTimeRecord \
            .select(XDFTimeRecord.map) \
            .where(XDFTimeRecord.server == server) \
            .distinct().count()

    @staticmethod
    def count_players(server):
        return (XDFTimeRecord
                .select(XDFTimeRecord.player)
                .where(XDFTimeRecord.server == server)
                .distinct().count())

    def get(self, request):
        servers = XDFServer.select().order_by(XDFServer.name)
        return render(request, 'xdf/servers.jinja', {
            'servers': servers,
            'current_nav_tab': 'servers',
            'count_maps': self.count_maps,
            'count_players': self.count_players
        })


class MapListView(View):
    def get_speed_record(self, servers, map_name):
        top_speed = 0
        record = None
        q = (XDFSpeedRecord.select(XDFPlayer.nickname.alias('nickname'),
                                   XDFPlayer.id.alias('player_id'),
                                   XDFSpeedRecord.speed.alias('speed'))
             .join(XDFPlayer)
             .where(XDFSpeedRecord.map == map_name))
        if servers:
            q = q.where(XDFSpeedRecord.server.in_(servers))
        for i in q.dicts():
            if i['speed'] > top_speed:
                record = i
        return record

    def get_time_record(self, servers, map_name):
        top_time = None
        record = None
        total_times = 0
        q = (XDFTimeRecord.select(XDFPlayer.nickname.alias('nickname'),
                                  XDFPlayer.id.alias('player_id'),
                                  XDFTimeRecord.time.alias('time'),
                                  XDFTimeRecord.video_url.alias('video_url'))
             .join(XDFPlayer)
             .where(XDFTimeRecord.map == map_name))
        if servers:
            q = q.where(XDFTimeRecord.server.in_(servers))
        for i in q.dicts():
            if top_time is None or i['time'] < top_time:
                top_time = i['time']
                record = i
            total_times += 1
        return total_times, record

    def get(self, request):
        form = MapListFilterForm(data=request.GET)
        if not form.is_valid():
            raise Http404()

        maps = XDFTimeRecord.select(XDFTimeRecord.map)
        servers = None

        if form.cleaned_data['maps']:
            maps = maps.where(XDFTimeRecord.map ** '%{}%'.format(form.cleaned_data['maps']))
        if form.cleaned_data['servers']:
            servers = form.cleaned_data['servers']
            maps = maps.where(XDFTimeRecord.server.in_(form.cleaned_data['servers']))

        total_maps = maps.count()
        maps = paginate_query(request, maps)
        maps = maps.distinct().tuples()

        table = []
        for i in maps:
            map_name = i[0]
            total_times, time_record = self.get_time_record(servers, map_name)
            table.append(
                {'map': map_name,
                 'time_record': time_record,
                 'total_times': total_times,
                 'speed_record': self.get_speed_record(servers, map_name)}
            )

        return render(request, 'xdf/maps.jinja', {
            'current_nav_tab': 'maps',
            'table': table,
            'form': form,
            'total_maps': total_maps
        })


class MapView(View):
    def get(self, request, map_name):
        form = MapFilterForm(data=request.GET)
        if not form.is_valid():
            raise Http404
        map_name = urllib.parse.unquote(map_name)
        servers = form.cleaned_data['servers']
        speed_records = (XDFSpeedRecord.select()
                         .where(XDFSpeedRecord.map == map_name)
                         .where(XDFSpeedRecord.server.in_(servers))
                         .order_by(XDFSpeedRecord.speed.desc()))
        speed_records_dedup = []
        players = set()
        for i in speed_records:
            if i.player not in players:
                speed_records_dedup.append(i)
                players.add(i.player)
        time_records_dedup = []
        players = set()
        time_records = (XDFTimeRecord.select()
                        .where(XDFTimeRecord.map == map_name)
                        .where(XDFTimeRecord.server.in_(servers))
                        .order_by(XDFTimeRecord.time, XDFTimeRecord.server_pos))
        for i in time_records:
            if i.player not in players:
                time_records_dedup.append(i)
                players.add(i.player)
        return render(request, 'xdf/map.jinja', {
            'current_nav_tab': 'maps',
            'map_name': map_name,
            'speed_records': speed_records_dedup,
            'time_records': time_records_dedup,
            'form': form
        })