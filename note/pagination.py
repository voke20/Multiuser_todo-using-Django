"""Note Pagination."""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class NotePagination(PageNumberPagination):
    """Page View all notes."""

    page_size = 6
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        """Return Note Pages."""
        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "results": data,
            }
        )


class CategoryPagination(PageNumberPagination):
    """Page view all notes."""

    page_size = 6
    page_size_query_params = 'page_size'
    max_page_size = 50

    def get_paginated_response(self, data):
        """Return Note Pages."""
        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "results": data,
            }
        )