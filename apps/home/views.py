from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator
from .models import Tutorial

# ========== HOME VIEW ========== #
@method_decorator(cache_page(60 * 1), name='dispatch')
class HomeView(TemplateView):
    """
    صفحه اصلی وبسایت
    """
    template_name = 'home/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ویدیوهای ویژه برای صفحه اصلی (اختیاری)
        context['featured_tutorials'] = Tutorial.objects.all()[:3]
        
        return context

# ========== CONTACT VIEW ========== #
@method_decorator(cache_page(60 * 1), name='dispatch') 
class ContactView(TemplateView):
    """
    صفحه ارتباط با ما
    """
    template_name = 'home/contact.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
# ========== ABOUT VIEW ========== #
@method_decorator(cache_page(60 * 1), name='dispatch')
class AboutView(TemplateView):
    """
    صفحه ارتباط با ما
    """
    template_name = 'home/about.html'

# ========== TUTORIAL LIST VIEW ========== #
@method_decorator(cache_page(60 * 30), name='dispatch')
class TutorialListView(TemplateView):
    """
    صفحه لیست ویدیوهای آموزشی
    """
    template_name = 'home/tutorials.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tutorials = Tutorial.get_all_tutorials()
        paginator = Paginator(tutorials, 9) 
        
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['tutorials'] = page_obj
        context['total_tutorials'] = tutorials.count()
        
        return context
    
# =========== PLAN LIST VIEW =========== #
@method_decorator(cache_page(60 * 1), name='dispatch')
class PlanListView(TemplateView):
    """
    صفحه ارتباط با ما
    """
    template_name = 'home/plan.html'
