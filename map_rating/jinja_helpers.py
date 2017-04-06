from django_jinja import library


@library.global_function
def query_param(request, param, value):
    old = request.GET.copy()
    old[param] = value
    return old.urlencode()


@library.global_function
def time_format(seconds):
    minutes = seconds // 60
    rest = seconds - minutes * 60
    if minutes == 0:
        return '%.2fs' % seconds
    else:
        return '%d:%.2f' % (minutes, rest)
