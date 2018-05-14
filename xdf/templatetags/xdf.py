import maya
from bootstrap4.forms import render_field
from django.utils.safestring import mark_safe
from django_jinja import library


@library.global_function
def bootstrap_field(*args, **kwargs):
    return render_field(*args, **kwargs)


@library.global_function
def format_timestamp(dt):
    mdt = maya.MayaDT.from_datetime(dt)
    return mark_safe('<abbr title="{}">{}</abbr>'.format(str(mdt), mdt.slang_time()))
