from django_jinja import library


@library.global_function
def query_param(request, param, value):
    old = request.GET.copy()
    old[param] = value
    return old.urlencode()
