from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page


# ========= Prescription List View ========= #
@method_decorator(cache_page(60 * 1), name='dispatch')
class PrescriptionListView(TemplateView):
    """
    صفحه ارتباط با ما
    """
    template_name = 'prescriptions/prescription_list.html'
    
# ========= Prescription Detail View ========= #
@method_decorator(cache_page(60 * 1), name='dispatch')
class PrescriptionDetailView(TemplateView):
    """
    صفحه ارتباط با ما
    """
    template_name = 'prescriptions/prescription_detail.html'
    
    def get_context_data(self, **kwargs):
        """
        این متد slug را از URL گرفته و به context تمپلیت اضافه می‌کند.
        """
        context = super().get_context_data(**kwargs)
        context['slug'] = kwargs.get('slug')
        return context
    

# ========= Prescription Content View ========= #
@method_decorator(cache_page(60 * 1), name='dispatch')
class PrescriptionContentView(TemplateView):
    """
    صفحه ارتباط با ما
    """
    template_name = 'prescriptions/prescription_content.html'
    
    def get_context_data(self, **kwargs):
        """
        این متد slug را از URL گرفته و به context تمپلیت اضافه می‌کند.
        """
        context = super().get_context_data(**kwargs)
        context['slug'] = kwargs.get('slug')
        return context


