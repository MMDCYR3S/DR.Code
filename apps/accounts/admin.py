from django.contrib import admin
from django.contrib.sessions.models import Session

from .models import Profile, User

# Register your models here.
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    search_fields = ('user__username',)
    
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass
