from rest_framework.pagination import PageNumberPagination


class CustomNumberPaginator(PageNumberPagination):
    page_size_query_param = "page_size"
    page_size = 10
