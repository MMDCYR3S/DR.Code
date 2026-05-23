from django.contrib import admin
from .models import Order, OrderSection, SectionItem, Condition, DrugSectionItem
# Register your models here.

admin.site.register(Order)
admin.site.register(OrderSection)
admin.site.register(SectionItem)
admin.site.register(Condition)
admin.site.register(DrugSectionItem)
