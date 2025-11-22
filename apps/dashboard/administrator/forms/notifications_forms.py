from django import forms
from django.contrib.auth import get_user_model
from apps.notifications.models import Notification, Announcement

User = get_user_model()

class SingleNotificationForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label="گیرنده",
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition duration-150 ease-in-out sm:text-sm',
        })
    )

    class Meta:
        model = Notification
        fields = ['recipient', 'title', 'message']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition duration-150 ease-in-out sm:text-sm',
                'placeholder': 'عنوان پیام را وارد کنید...'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition duration-150 ease-in-out sm:text-sm',
                'rows': 4,
                'placeholder': 'متن پیام خود را بنویسید...'
            }),
        }

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'message', 'target_role']
        widgets = {
            'target_role': forms.Select(attrs={
                'class': 'w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition duration-150 ease-in-out sm:text-sm',
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition duration-150 ease-in-out sm:text-sm',
                'placeholder': 'عنوان اطلاعیه عمومی...'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition duration-150 ease-in-out sm:text-sm',
                'rows': 4,
                'placeholder': 'متن اطلاعیه را بنویسید...'
            }),
        }
