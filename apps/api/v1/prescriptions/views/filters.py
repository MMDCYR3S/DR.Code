# filters.py
import django_filters
from django.db.models import Q
from apps.prescriptions.models import Prescription, PrescriptionCategory

class PrescriptionFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method='filter_search', 
        label='جستجو در نام و توضیحات'
    )
    
    category = django_filters.ModelChoiceFilter(
        queryset=PrescriptionCategory.objects.all(),
        field_name='category',
        to_field_name='id',
        empty_label="همه دسته‌ها",
        label='دسته‌بندی'
    )
    
    access_level = django_filters.ChoiceFilter(
        choices=[('', 'همه'), ('FREE', 'رایگان'), ('PREMIUM', 'ویژه')],
        field_name='access_level',
        empty_label=None,
        label='سطح دسترسی'
    )
    
    class Meta:
        model = Prescription
        fields = ['category', 'access_level']
    
    def filter_search(self, queryset, name, value):
        """جستجو در نام اصلی، نام‌های جایگزین و توضیحات"""
        if value:
            return queryset.filter(
                Q(title__icontains=value) |
                Q(aliases__name__icontains=value) |
                Q(detailed_description__icontains=value)
            ).distinct()
        return queryset
