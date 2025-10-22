from apps.accounts.models import AuthStatusChoices

def auth_status_processor(request):
    """
    یک Context Processor برای بررسی وضعیت احراز هویت و تصمیم‌گیری برای نمایش نوار هشدار.
    """
    show_warning = False

    if request.user.is_authenticated:
        try:
            profile = request.user.profile

            if profile.auth_status == AuthStatusChoices.REJECTED:
                show_warning = True
            elif profile.auth_status == AuthStatusChoices.PENDING:
                has_documents = profile.documents.exists()
                
                if not has_documents:
                    show_warning = True
                    
        except AttributeError:
            show_warning = True

    return {
        'show_auth_warning': show_warning
    }