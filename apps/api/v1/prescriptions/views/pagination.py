from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict

class PrescriptionPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('page_size', self.get_page_size(self.request)),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('first', self.get_first_link()),
            ('last', self.get_last_link()),
            ('results', data)
        ]))
    
    def get_first_link(self):
        if not self.page.has_previous():
            return None
        url = self.request.build_absolute_uri()
        return self.replace_query_param(url, self.page_query_param, 1)
    
    def get_last_link(self):
        if not self.page.has_next():
            return None
        url = self.request.build_absolute_uri()
        return self.replace_query_param(
            url, self.page_query_param, self.page.paginator.num_pages
        )

    def replace_query_param(self, url, key, val):
        """Helper method برای جایگزینی query parameter"""
        from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse
        
        parsed = urlparse(url)
        params = dict(parse_qsl(parsed.query))
        params[key] = val
        new_query = urlencode(params)
        return urlunparse(parsed._replace(query=new_query))