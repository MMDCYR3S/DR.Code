from django.views.generic import TemplateView


# ========= Order List View ========= #
class OrderListView(TemplateView):
    """
    صفحه لیست اوردرینگ پزشکی‌ها
    """
    template_name = 'ordering/ordering_list.html'
    

# ========= Order Detail View ========= #
class OrderDetailView(TemplateView):
    """
    صفحه جزئیات اوردرینگ پزشکی
    """
    template_name = 'ordering/ordering_detail.html'
    
    def get_context_data(self, **kwargs):
        """
        این متد slug را از URL گرفته و به context تمپلیت اضافه می‌کند.
        """
        context = super().get_context_data(**kwargs)
        context['slug'] = kwargs.get('slug')
        return context
