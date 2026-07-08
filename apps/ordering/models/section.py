import jdatetime
from django_ckeditor_5.fields import CKEditor5Field

from django.db import models

from .order import Order
from .colors import TailwindColor

class OrderSection(models.Model):
    """
    زیرمجموعه‌های پویای هر Order.
    هر Order می‌تواند چندین Section داشته باشد.
    هفت Section پیش‌فرض در زمان نصب اولیه از طریق data migration ثبت می‌شوند.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="sections",
        verbose_name="Order مرجع"
    )
    title = models.CharField(
        max_length=200,
        verbose_name="عنوان Section",
        help_text='مثال: "Monitoring & nursing"، "Drugs"، "Imaging"'
    )
    notes = CKEditor5Field(
        blank=True, 
        verbose_name="توضیحات کلی Section", 
        help_text="توضیحاتی که به کل Section مربوط است، نه به یک آیتم خاص",
        config_name='default'
    )
    is_drug_section = models.BooleanField(
        default=False,
        verbose_name="بخش داروهاست؟",
        help_text="در صورت فعال بودن، امکان انتخاب دارو از بانک داروهای موجود فعال می‌شود"
    )
    order_index = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش"
    )

    # ─────────────────────────── رنگ‌بندی ────────────────────────────────
    color = models.CharField(
        max_length=30,
        choices=TailwindColor.choices,
        blank=True,
        verbose_name="رنگ Section",
        help_text="رنگ نمایشی این Section در رابط کاربری"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ساخت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="زمان بروزرسانی")

    class Meta:
        verbose_name = "Section"
        verbose_name_plural = "Sections"
        ordering = ["order_index"]

    def __str__(self):
        return f"{self.title} (Order: {self.order_id})"

    @property
    def shamsi_created_at(self):
        if self.created_at is None:
            return "—"
        jdate = jdatetime.datetime.fromgregorian(datetime=self.created_at)
        return jdate.strftime("%Y/%m/%d - %H:%M")

    @property
    def shamsi_updated_at(self):
        if self.updated_at is None:
            return "—"
        jdate = jdatetime.datetime.fromgregorian(datetime=self.updated_at)
        return jdate.strftime("%Y/%m/%d - %H:%M")
    
    @property
    def all_conditions(self):
        """
        تمام شرط‌های منحصر‌به‌فردِ مربوط به آیتم‌های عادی و داروهای این سکشن را جمع‌آوری می‌کند.
        """
        print(f"\n[DEBUG] === Start all_conditions for Section: {self.title} (ID: {self.id}) ===")
        condition_ids = set()

        # واکشی شرط‌های آیتم‌ها
        items = self.items.all()
        print(f"[DEBUG] Found {items.count()} text items in this section.")
        for item in items:
            for condition in item.conditions.all():
                print(f"[DEBUG] -> Text Item (ID: {item.id}) has Condition ID: {condition.id}")
                condition_ids.add(condition.id)
                
        # واکشی شرط‌های داروها
        drug_items = self.drug_items.all()
        print(f"[DEBUG] Found {drug_items.count()} drug items in this section.")
        for drug_item in drug_items:
            for condition in drug_item.conditions.all():
                print(f"[DEBUG] -> Drug Item (ID: {drug_item.id}) has Condition ID: {condition.id}")
                condition_ids.add(condition.id)
        
        print(f"[DEBUG] Total unique condition IDs collected: {list(condition_ids)}")
        
        if not condition_ids:
            print("[DEBUG] === No conditions found. Returning empty queryset. ===\n")
            return Condition.objects.none()

        queryset = Condition.objects.filter(id__in=condition_ids).order_by('order_index')
        print(f"[DEBUG] === Successfully returning {queryset.count()} conditions. ===\n")
        return queryset


class LogicalOperator(models.TextChoices):
    """ Enum برای اپراتورهای منطقی بین آیتم‌ها """
    OR = 'OR', 'یا (OR)'
    AND = 'AND', 'و (AND)'
    THEN = 'THEN', 'و (THEN)'

class ItemRelationshipGroup(models.Model):
    """
    یک گروه برای مرتبط کردن چند آیتم در یک سکشن با یک اپراتور منطقی.
    مثال: (آیتم ۱ OR آیتم ۲ OR آیتم ۳) در سکشن X.
    """
    section = models.ForeignKey(
        OrderSection,
        on_delete=models.CASCADE,
        related_name="relationship_groups",
        verbose_name="سکشن مرجع"
    )
    operator = models.CharField(
        max_length=10,
        choices=LogicalOperator.choices,
        default=LogicalOperator.OR,
        verbose_name="اپراتور منطقی"
    )
    order_index = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش گروه"
    )

    class Meta:
        verbose_name = "گروه ارتباطی آیتم‌ها"
        verbose_name_plural = "گروه‌های ارتباطی آیتم‌ها"
        ordering = ['order_index']

    def __str__(self):
        return f"گروه {self.get_operator_display()} در سکشن {self.section.title}"

# ─────────────────────────────────────────────────────────────────────────────

class Condition(models.Model):
    """
    شرط‌های مشترک که می‌توانند روی چندین آیتم اعمال شوند.
    """
    text = models.TextField(
        verbose_name="متن شرط",
        help_text='مثال: "if SBP≥90, PR≥60"، "در صورت تهوع"'
    )
    order_index = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ساخت")

    class Meta:
        verbose_name = "شرط"
        verbose_name_plural = "شرط‌ها"
        ordering = ["order_index"]

    def __str__(self):
        return f"شرط: {self.text[:80]}"


class SectionItem(models.Model):
    section = models.ForeignKey(
        OrderSection,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Section مرجع"
    )
    text = models.TextField(verbose_name="متن آیتم")
    notes = CKEditor5Field(blank=True, verbose_name="توضیحات اختصاصی آیتم", config_name='default')
    order_index = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")

    conditions = models.ManyToManyField(
        Condition,
        related_name="section_items",
        blank=True,
        verbose_name="شرط‌ها"
    )

    relationship_group = models.ForeignKey(
        ItemRelationshipGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="text_items",
        verbose_name="گروه ارتباطی"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ساخت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="زمان بروزرسانی")

    class Meta:
        verbose_name = "آیتم Section"
        verbose_name_plural = "آیتم‌های Section"
        ordering = ["order_index"]

    def __str__(self):
        return f"{self.text[:80]} — {self.section.title}"


class DrugSectionItem(models.Model):
    section = models.ForeignKey(
        OrderSection,
        on_delete=models.CASCADE,
        related_name="drug_items",
        verbose_name="Section مرجع"
    )
    drug = models.ForeignKey(
        "prescriptions.Drug",
        on_delete=models.CASCADE,
        related_name="order_drug_items",
        verbose_name="داروی انتخابی"
    )
    notes = CKEditor5Field(blank=True, verbose_name="توضیحات اضافی دارو در این Order", config_name='default')
    order_index = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")
    
    conditions = models.ManyToManyField(
        Condition,
        related_name="drug_items",
        blank=True,
        verbose_name="شرط‌ها"
    )

    relationship_group = models.ForeignKey(
        ItemRelationshipGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="drug_items",
        verbose_name="گروه ارتباطی"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ساخت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="زمان بروزرسانی")

    class Meta:
        verbose_name = "دارو در Section"
        verbose_name_plural = "داروهای Section"
        ordering = ["order_index"]

    def __str__(self):
        return f"داروی «{self.drug.title}» در Section «{self.section.title}»"
