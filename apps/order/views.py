from django.views.generic import TemplateView

# =========== PLAN ORDER VIEW =========== #
class PlanOrderView(TemplateView):
    """
    صفحه ارتباط با ما
    """
    template_name = 'order/checkout.html'
