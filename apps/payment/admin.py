from django.contrib import admin
from .models import Payment

# Register your models here.
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_filter=("status", "created_at")
    list_display=("status", "amount", "user", "created_at")