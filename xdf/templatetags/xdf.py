import urllib.parse

import maya
from bootstrap4.forms import render_field
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import mark_safe
from django_jinja import library


@library.global_function
def bootstrap_field(*args, **kwargs):
    return render_field(*args, **kwargs)


@library.global_function
def format_timestamp(dt):
    mdt = maya.MayaDT.from_datetime(dt)
    return mark_safe('<abbr title="{}">{}</abbr>'.format(str(mdt), mdt.slang_time()))


@library.global_function
def format_time(time):
    if time < 60:
        return "{:0>5.2f}".format(time)
    else:
        minutes = time // 60
        seconds = time % 60
        return "{}:{:0>5.2f}".format(minutes, seconds)


@library.global_function
def render_pagination(request, total):
    try:
        page_number = int(request.GET.get('page_number'))
    except (TypeError, ValueError):
        page_number = 1
    try:
        page_size = int(request.GET.get('page_size'))
    except (TypeError, ValueError):
        page_size = settings.DEFAULT_PAGE_SIZE

    qd = request.GET.copy()
    qd['page_number'] = page_number - 1
    prev_link = qd.urlencode()
    qd['page_number'] = page_number + 1
    next_link = qd.urlencode()
    return render_to_string('xdf/_pagination.jinja', {
        'prev_link': prev_link,
        'current_page': page_number,
        'next_link': next_link,
        'total_pages': total // page_size + 1,
    })


@library.global_function
def urlquote(s):
    return urllib.parse.quote(s)


@library.global_function
def login_url(request):
    return_url = request.path
    return reverse('login') + '?next={}'.format(return_url)
