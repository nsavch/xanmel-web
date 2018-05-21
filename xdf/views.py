import urllib.parse
from collections import OrderedDict

from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import render
from django.conf import settings
from django.urls import reverse
from django.views import View
from peewee import fn

from xanmel.modules.xonotic.models import *
from xdf.templatetags.xdf import format_time

from .forms import NewsFeedFilterForm, MapListFilterForm, MapFilterForm, LadderFilterForm, CompareWithForm, \
    SearchPlayerForm, SearchType, PlayerRecordSearchForm
from .utils import paginate_query


def format_player_with_link(player):
    return '<a href="{}">{}</a>'.format(
        reverse('xdf:player', args=(player.id,)),
        player.nickname
    )


class HelpersMixin:
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
                yt_link = '{}s'.format(format_time(news_item.time_record.time), )
            return "{} set time &mdash; {} (server {}/{}, global {}/{})".format(
                format_player_with_link(news_item.time_record.player),
                yt_link,
                news_item.time_record.server_pos,
                news_item.time_record.server_max_pos,
                news_item.time_record.global_pos,
                news_item.time_record.global_max_pos,
            )

    @staticmethod
    def count_rest(data):
        res = 0
        for i in range(11, 101):
            res += data.get(str(i), 0)
        return res


class IndexView(View, HelpersMixin):

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
                top_speed = i['speed']
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

        maps = XDFTimeRecord.select(XDFTimeRecord.map).order_by(XDFTimeRecord.map)
        servers = None

        if form.cleaned_data['maps']:
            maps = maps.where(XDFTimeRecord.map ** '%{}%'.format(form.cleaned_data['maps']))
        if form.cleaned_data['servers']:
            servers = form.cleaned_data['servers']
            maps = maps.where(XDFTimeRecord.server.in_(form.cleaned_data['servers']))

        maps = maps.distinct()
        total_maps = maps.count()
        maps = paginate_query(request, maps)
        maps = maps.tuples()

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
                        .order_by(XDFTimeRecord.time, XDFTimeRecord.server_pos, SQL('video_url DESC NULLS LAST')))
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


class ClassicLadderView(View, HelpersMixin):
    def get(self, request):
        form = LadderFilterForm(data=request.GET)
        form.is_valid()
        t = form.cleaned_data['ladder_type'] and int(form.cleaned_data['ladder_type']) or LadderType.GLOBAL.value
        s = form.cleaned_data['server']
        players = form.cleaned_data['players']

        if t == LadderType.GLOBAL.value:
            try:
                ladder = XDFLadder.get(XDFLadder.algo == LadderAlgo.CLASSIC.value,
                                       XDFLadder.type == LadderType.GLOBAL.value)
            except DoesNotExist:
                raise Http404()
            positions = (XDFLadderPosition.select()

                         .where(XDFLadderPosition.ladder == ladder)
                         .order_by(XDFLadderPosition.position))
        else:
            try:
                ladder = XDFLadder.get(XDFLadder.algo == LadderAlgo.CLASSIC.value,
                                       XDFLadder.type == LadderType.SERVER.value,
                                       XDFLadder.server == s)
            except DoesNotExist:
                raise Http404
            positions = (XDFLadderPosition.select()
                         .join(XDFLadder)
                         .where(XDFLadderPosition.ladder == ladder)
                         .order_by(XDFLadderPosition.position))
        if players:
            positions = positions.switch(XDFLadderPosition).join(XDFPlayer).where(
                XDFPlayer.nickname ** '%{}%'.format(players))
        total_positions = positions.count()
        positions = paginate_query(request, positions)
        columns = [str(i) for i in range(1, 11)]

        return render(request, 'xdf/ladder_classic.jinja', {
            'current_nav_tab': 'players',
            'ladder': ladder,
            'positions': positions,
            'columns': columns,
            'total_positions': total_positions,
            'form': form,
            'count_rest': self.count_rest
        })


class PlayerView(View, HelpersMixin):

    def get(self, request, player_id):
        try:
            player = XDFPlayer.get(id=player_id)
        except DoesNotExist:
            raise Http404
        compare_form = CompareWithForm(initial={'player1': player.id})
        ladder_positions = (XDFLadderPosition.select()
                            .join(XDFLadder)
                            .where(XDFLadderPosition.player == player)
                            .order_by(XDFLadder.type))
        news_items = (XDFNewsFeed.select()
                      .join(XDFTimeRecord, JOIN_LEFT_OUTER)
                      .switch(XDFNewsFeed)
                      .join(XDFSpeedRecord, JOIN_LEFT_OUTER)
                      .where((XDFTimeRecord.player == player) | (XDFSpeedRecord.player == player))
                      .order_by(XDFNewsFeed.timestamp.desc()))[:10]
        ladder_columns = [str(i) for i in range(1, 11)]
        best_records = (XDFTimeRecord.select()
                        .where(XDFTimeRecord.player == player)
                        .order_by(XDFTimeRecord.global_pos.asc(), XDFTimeRecord.global_max_pos.desc()))[:10]
        keys = XDFPlayerKey.select().where(XDFPlayerKey.player == player)

        return render(request, 'xdf/player.jinja', {
            'player': player,
            'current_nav_tab': 'players',
            'ladder_positions': ladder_positions,
            'news_items': news_items,
            'ladder_columns': ladder_columns,
            'count_rest': self.count_rest,
            'format_news_item': self.format_news_item,
            'best_records': best_records,
            'compare_form': compare_form,
            'keys': keys
        })


class CompareView(View):
    def get(self, request):
        try:
            player1_id = int(request.GET['player1'])
            player2_id = int(request.GET['player2'])
        except (KeyError, TypeError, ValueError):
            return HttpResponseBadRequest()
        try:
            player1 = XDFPlayer.get(id=player1_id)
            player2 = XDFPlayer.get(id=player2_id)
        except DoesNotExist:
            raise Http404()

        records = (XDFTimeRecord.select()
                   .where(XDFTimeRecord.player == player1 | XDFTimeRecord.player == player2)
                   .order_by(XDFTimeRecord.map))

        tr_tbl1 = XDFTimeRecord.alias()
        tr_tbl2 = XDFTimeRecord.alias()

        q = (tr_tbl1.select(tr_tbl1.map,
                            tr_tbl1.global_pos,
                            tr_tbl1.global_max_pos,
                            tr_tbl1.time,
                            tr_tbl2.global_pos,
                            tr_tbl2.time)
             .join(tr_tbl2, on=(tr_tbl1.map == tr_tbl2.map))
             .where(tr_tbl1.player == player1, tr_tbl2.player == player2)
             .order_by(tr_tbl1.map)).tuples()
        results = []
        summary = {
            'p1_better': 0,
            'p2_better': 0,
            'total_gap': 0
        }
        times1 = {}
        times2 = {}

        for m, p1, mp, t1, p2, t2 in q:
            if m not in times1 or times1[m] > t1:
                times1[m] = t1
            if m not in times2 or times2[m] > t2:
                times2[m] = t2

        for m, p1, mp, t1, p2, t2 in q:
            if times1[m] != t1 or times2[m] != t2:
                continue
            if t1 < t2:
                summary['p1_better'] += 1
                gap = (t2 - t1) * 100 / t1
                summary['total_gap'] += gap
            else:
                summary['p2_better'] += 1
                gap = (t1 - t2) * 100 / t2
                summary['total_gap'] -= gap
            results.append((m, p1, mp, t1, p2, t2, gap))

        return render(request, 'xdf/compare.jinja', {
            'current_nav_tab': 'players',
            'player1': player1,
            'player2': player2,
            'records': records,
            'results': results,
            'summary': summary
        })


class PlayerActivityView(View):
    def get(self, request, player_id):
        try:
            player = XDFPlayer.get(id=player_id)
        except DoesNotExist:
            raise Http404
        form = NewsFeedFilterForm(data=request.GET)
        form.is_valid()
        news_items = (XDFNewsFeed.select()
                      .join(XDFTimeRecord, JOIN_LEFT_OUTER)
                      .switch(XDFNewsFeed)
                      .join(XDFSpeedRecord, JOIN_LEFT_OUTER)
                      .where((XDFTimeRecord.player == player) | (XDFSpeedRecord.player == player))
                      .order_by(XDFNewsFeed.timestamp.desc()))
        if form.cleaned_data['maps']:
            pattern = '%{}%'.format(form.cleaned_data['maps'])
            news_items = news_items.where(XDFTimeRecord.map ** pattern | XDFSpeedRecord.map ** pattern)
        servers = form.cleaned_data['servers']
        news_items = news_items.where(XDFTimeRecord.server.in_(servers) | XDFSpeedRecord.server.in_(servers))
        news_items = news_items.where(XDFNewsFeed.event_type.in_(form.cleaned_data['event_types']))
        if form.cleaned_data['position_lte']:
            news_items = news_items.where(XDFTimeRecord.server_pos <= form.cleaned_data['position_lte'])
        total_news_items = news_items.count()
        news_items = paginate_query(request, news_items)
        return render(request, 'xdf/player_activity.jinja', {
            'current_nav_tab': 'players',
            'player': player,
            'news_items': news_items,
            'total_news_items': total_news_items,
            'form': form
        })


class PlayerSpeedRecordsView(View):
    def get(self, request, player_id):
        try:
            player = XDFPlayer.get(id=player_id)
        except DoesNotExist:
            raise Http404
        records = OrderedDict()
        raw_records = (XDFSpeedRecord.select()
                       .where(XDFSpeedRecord.player == player)
                       .order_by(XDFSpeedRecord.map))
        for i in raw_records:
            if i.map not in records or records[i.map].speed < i.speed:
                records[i.map] = i

        return render(request, 'xdf/player_speed_records.jinja', {
            'current_nav_tab': 'players',
            'player': player,
            'records': records
        })


class PlayerTimeRecordsView(View):
    def get(self, request, player_id):
        try:
            player = XDFPlayer.get(id=player_id)
        except DoesNotExist:
            raise Http404
        form = PlayerRecordSearchForm(data=request.GET)
        form.is_valid()
        records = (XDFTimeRecord.select()
                   .where(XDFTimeRecord.player == player,
                          XDFTimeRecord.server.in_(form.cleaned_data['servers']))
                   .order_by(XDFTimeRecord.map))
        cd = form.cleaned_data
        if cd['maps']:
            records = records.where(XDFTimeRecord.map ** '%{}%'.format(cd['maps']))
        if cd['position_gte']:
            records = records.where(XDFTimeRecord.server_pos >= cd['position_gte'])
        if cd['position_lte']:
            records = records.where(XDFTimeRecord.server_pos <= cd['position_lte'])
        total_records = records.count()
        records = paginate_query(request, records)
        return render(request, 'xdf/player_time_records.jinja', {
            'current_nav_tab': 'players',
            'player': player,
            'records': records,
            'form': form,
            'total_records': total_records
        })


class AdvancedPlayerSearchView(View):
    def get(self, request):
        players = None
        searched = False
        if request.GET:
            form = SearchPlayerForm(request.GET)
            players = XDFPlayer.select().join(XDFPlayerKey).join(XDFPlayerNickname)
            if form.is_valid():
                searched = True
                qt = form.cleaned_data['query_type']
                q = form.cleaned_data['query']
                pattern = '%{}%'.format(q)
                if qt == SearchType.CRYPTO_IDFP.value:
                    players = players.where(XDFPlayerKey.crypto_idfp ** pattern)
                elif qt == SearchType.STATS_ID.value:
                    players = players.where(XDFPlayer.stats_id == q)
                else:
                    players = players.where(
                        XDFPlayerNickname.nickname ** pattern | XDFPlayerNickname.raw_nickname ** pattern)
                players = set(players)
                players = sorted(list(players), key=lambda x: x.nickname)

        else:
            form = SearchPlayerForm()

        return render(request, 'xdf/player_search.jinja', {
            'current_nav_tab': 'players',
            'form': form,
            'players': players,
            'searched': searched
        })
