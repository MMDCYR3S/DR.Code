from django.views.generic import TemplateView

# =========== PLAN ORDER VIEW =========== #
class PlanOrderView(TemplateView):
    """
    صفحه ارتباط با ما
    """
    template_name = 'order/checkout.html'

    def get_context_data(self, **kwargs):
        """فقط plan_id را به تمپلیت پاس می‌دهد"""
        context = super().get_context_data(**kwargs)
        context['plan_id'] = kwargs.get('plan_id')
        return context
