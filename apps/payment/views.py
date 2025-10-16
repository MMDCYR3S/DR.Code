from django.views.generic import TemplateView

# ======= REQUEST VIEW ======= #
class RequestView(TemplateView):
    """ نمایش وضعیت پرداخت بعد از درگاه پرداخت """
    
    template_name = "payment/request.html"
# ======= AFTER PAY VIEW ======= #
class AfterPayView(TemplateView):
    """ نمایش وضعیت پرداخت بعد از درگاه پرداخت """
    template_name = "payment/after_pay.html"
