from django.utils import timezone

class SubscriptionCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        
        if user.is_authenticated and hasattr(user, 'profile'):
            profile = user.profile

            if profile.role == "premium" and profile.subscription_end_date:
                if timezone.now() > profile.subscription_end_date:
                    profile.role = "regular"
                    profile.subscription_end_date = None
                    profile.save(update_fields=['role', 'subscription_end_date'])

        response = self.get_response(request)
        return response