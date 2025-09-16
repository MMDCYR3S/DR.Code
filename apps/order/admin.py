from django.contrib import admin
from .models import DiscountCode

# Register your models here.
@admin.register(DiscountCode)
class AdminDiscount(admin.ModelAdmin):
    pass