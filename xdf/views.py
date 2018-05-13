from django.http import Http404
from django.shortcuts import render
from django.conf import settings
from django.views import View
from peewee import fn

from xanmel.modules.xonotic.models import *


def format_player_with_link(player):
    return "{}".format(player.nickname)


class IndexView(View):
    @staticmethod
    def format_news_item(news_item):
        if news_item.event_type == EventType.SPEED_RECORD.value:
            return "{}"

    def get(self, request):
        servers = XDFServer.select()
        news = XDFNewsFeed.select().order_by(XDFNewsFeed.timestamp.desc())
        return render(request, 'xdf/index.jinja', {
            'servers': servers,
            'news': news
        })
