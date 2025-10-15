from django.views.generic import TemplateView

# ======= AFTER PAY VIEW ======= #
class RequestView(TemplateView):
    """ نمایش وضعیت پرداخت بعد از درگاه پرداخت """
    template_name = "payment/request.html"
