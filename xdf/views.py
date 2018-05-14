from django.http import Http404
from django.shortcuts import render
from django.conf import settings
from django.views import View
from peewee import fn

from xanmel.modules.xonotic.models import *

from .forms import NewsFeedFilterForm


def format_player_with_link(player):
    return "{}".format(player.nickname)


def format_time(time):
    if time < 60:
        return "{:.2f}".format(time)
    else:
        minutes = time // 60
        seconds = time % 60
        return "{}:{:.2f}".format(minutes, seconds)


class IndexView(View):
    @staticmethod
    def format_news_item(news_item):
        if news_item.event_type == EventType.SPEED_RECORD.value:
            return "{} set high speed record &mdash; {}".format(
                format_player_with_link(news_item.speed_record.player),
                news_item.speed_record.speed
            )
        elif news_item.event_type == EventType.TIME_RECORD.value:
            return "{} set time {} (server {}/{}, global {}/{})".format(
                format_player_with_link(news_item.time_record.player),
                format_time(news_item.time_record.time),
                news_item.time_record.server_pos,
                news_item.time_record.server_max_pos,
                news_item.time_record.global_pos,
                news_item.time_record.global_max_pos,
            )

    def get(self, request):
        filter_form = NewsFeedFilterForm()
        news = XDFNewsFeed.filter_feed()[:50]
        return render(request, 'xdf/index.jinja', {
            'form': filter_form,
            'news': news,
            'format_news_item': self.format_news_item,
            'current_nav_tab': 'index'
        })


class ServerListView(View):
    @staticmethod
    def count_maps(server):
        return XDFTimeRecord\
            .select(XDFTimeRecord.map)\
            .where(XDFTimeRecord.server == server)\
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
    def get(self, request):
        return render(request, 'xdf/maps.jinja', {
            'current_nav_tab': 'maps'
        })
