from django.views.generic import TemplateView

# ======= AFTER PAY VIEW ======= #
class AfterPayView(TemplateView):
    """ نمایش وضعیت پرداخت بعد از درگاه پرداخت """
    template_name = "payment/after_pay.html"
