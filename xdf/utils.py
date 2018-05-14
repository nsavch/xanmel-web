from django.conf import settings


def paginate_query(request, query):
    try:
        page_number = int(request.GET.get('page_number'))
    except (TypeError, ValueError):
        page_number = 1
    try:
        page_size = int(request.GET.get('page_size'))
    except (TypeError, ValueError):
        page_size = settings.DEFAULT_PAGE_SIZE
    return query.paginate(page_number, page_size)
