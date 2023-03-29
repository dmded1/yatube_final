from django.core.paginator import Paginator


def get_pagination_context(queryset, request):
    posts_per_page = 10
    paginator = Paginator(queryset, posts_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
