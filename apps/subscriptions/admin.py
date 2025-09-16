from django.contrib import admin
from .models import Subscription, Plan, Membership

# Register your models here.
@admin.register(Membership)
class AdminMem(admin.ModelAdmin):
    pass

@admin.register(Plan)
class AdminPlan(admin.ModelAdmin):
    pass