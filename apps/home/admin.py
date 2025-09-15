from django.contrib import admin
from .models import Contact, Tutorial

# Register your models here.
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    pass

# Tutorial
@admin.register(Tutorial)
class TutorialAdmin(admin.ModelAdmin):
    pass