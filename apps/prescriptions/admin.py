from django.contrib import admin
from .models import Prescription, PrescriptionAlias, PrescriptionDrug, PrescriptionCategory, PrescriptionImage, PrescriptionVideo

class PrescriptionAliasInline(admin.TabularInline):
    model = PrescriptionAlias
    extra = 1
    fields = ('name', 'is_primary')
    readonly_fields = ('created_at',)

@admin.register(PrescriptionAlias)
class PrescriptionAliasAdmin(admin.ModelAdmin):
    list_display = ('name', 'prescription', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('name', 'prescription__title')
    list_editable = ('is_primary',)

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    inlines = [PrescriptionAliasInline]
    list_display = ('title', 'category', 'get_aliases_count', 'access_level', 'is_active')
    list_filter = ('category', 'access_level', 'is_active')
    search_fields = ('title', 'aliases__name')
    
    def get_aliases_count(self, obj):
        return obj.aliases.count()
    get_aliases_count.short_description = 'تعداد نام‌های جایگزین'

@admin.register(PrescriptionVideo)
class AdminVideo(admin.ModelAdmin):
    pass

@admin.register(PrescriptionCategory)
class AdminCat(admin.ModelAdmin):
    pass

@admin.register(PrescriptionImage)
class AdminImage(admin.ModelAdmin):
    pass

@admin.register(PrescriptionDrug)
class PrescriptionDrugAdmin(admin.ModelAdmin):
    pass
