from django.urls import reverse_lazy
from django.db import transaction
from django.contrib import messages
from apps.prescriptions.models import Prescription
from ..forms import PrescriptionForm, DrugFormSet, AliasFormSet, ImageFormSet, VideoFormSet
from apps.prescriptions.models import *

class PrescriptionFormMixin:
    model = Prescription
    form_class = PrescriptionForm
    template_name = 'dashboard/prescriptions/prescription-form.html'

    def get_success_url(self):
        messages.success(self.request, f"نسخه «{self.object.title}» با موفقیت ذخیره شد.")
        return reverse_lazy('dashboard:prescriptions:prescription_list')

    def form_valid(self, form):
        with transaction.atomic():
            # ذخیره فرم اصلی
            self.object = form.save()
            
            # پردازش داده‌های related objects
            self.process_drugs()
            self.process_aliases()
            self.process_videos()
            self.process_images()
            
            # چک کردن action
            action = self.request.POST.get('action', 'save_draft')
            if action == 'publish':
                self.object.is_active = True
                self.object.save()
        
        return super().form_valid(form)

    def process_drugs(self):
        self.object.drugs.all().delete()
        
        drug_count = 0
        while f'drug_{drug_count}_title' in self.request.POST:
            title = self.request.POST.get(f'drug_{drug_count}_title', '').strip()
            if title:
                PrescriptionDrug.objects.create(
                    prescription=self.object,
                    title=title,
                    code=self.request.POST.get(f'drug_{drug_count}_code', ''),
                    dosage=self.request.POST.get(f'drug_{drug_count}_dosage', ''),
                    amount=int(self.request.POST.get(f'drug_{drug_count}_amount', 0) or 0),
                    instructions=self.request.POST.get(f'drug_{drug_count}_instructions', ''),
                    is_combination=self.request.POST.get(f'drug_{drug_count}_is_combination') == 'true',
                    combination_group=self.request.POST.get(f'drug_{drug_count}_combination_group', ''),
                    order=drug_count + 1
                )
            drug_count += 1

    def process_aliases(self):
        self.object.aliases.all().delete()
        
        alias_count = 0
        while f'alias_{alias_count}_name' in self.request.POST:
            name = self.request.POST.get(f'alias_{alias_count}_name', '').strip()
            if name:
                PrescriptionAlias.objects.create(
                    prescription=self.object,
                    name=name,
                    is_primary=self.request.POST.get(f'alias_{alias_count}_is_primary') == 'true'
                )
            alias_count += 1

    def process_videos(self):
        self.object.videos.all().delete()
        
        video_count = 0
        while f'video_{video_count}_url' in self.request.POST:
            url = self.request.POST.get(f'video_{video_count}_url', '').strip()
            if url:
                from apps.prescriptions.models import PrescriptionVideo  # Import مدل
                PrescriptionVideo.objects.create(
                    prescription=self.object,
                    video_url=url,
                    title=self.request.POST.get(f'video_{video_count}_title', ''),
                    description=self.request.POST.get(f'video_{video_count}_description', '')
                )
            video_count += 1

    def process_images(self):
        image_count = 0
        while f'image_{image_count}' in self.request.FILES:
            image_file = self.request.FILES.get(f'image_{image_count}')
            if image_file:
                PrescriptionImage.objects.create(
                    prescription=self.object,
                    image=image_file,
                    caption=self.request.POST.get(f'image_{image_count}_caption', '')
                )
            image_count += 1
