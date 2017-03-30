from django.conf import settings

from xanmel.db import XanmelDB


class XanmelDBMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.__db = XanmelDB(settings.XANMEL_CONFIG['settings']['db_url'])
        request.__db.db.connect()
        response = self.get_response(request)
        if not request.__db.db.is_closed():
            request.__db.db.close()
        return response
