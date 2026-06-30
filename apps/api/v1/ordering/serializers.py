from django.urls import reverse
from rest_framework import serializers
from apps.ordering.models import (
    Order, OrderSection, Condition, SectionItem, DrugSectionItem,
    EmergencyDisposition, EmergencyNode, DynamicFieldGroup, DynamicFieldNode,
    OrderImage, OrderVideo, ItemRelationshipGroup, OrderAlias,
)
from apps.prescriptions.models import Drug, PrescriptionCategory


def build_item_numbering(order_instance):
    """
    شماره‌گذاری global و پیوسته برای تمام آیتم‌های یک Order.
    کلید: (item_type, item_id) — مقدار: عدد ترتیبی از 1
    item_type: 'text' یا 'drug'

    ترتیب نمایش/شماره‌گذاری در هر سکشن:
      1) آیتم‌های مستقل (بدون relationship_group) و گروه‌های منطقی (OR/AND/THEN)
         همگی بر اساس order_index خودشان به‌صورت یکجا مرتب می‌شوند.
      2) داخل هر گروه منطقی، آیتم‌های متنی و دارویی به ترتیب درج شماره می‌گیرند.
    این تابع از داده‌های از پیش prefetch‌شده (obj.sections.all() و ...) استفاده
    می‌کند و هیچ کوئری اضافه‌ای به دیتابیس نمی‌زند.
    """
    numbering = {}
    counter = 1

    sections = sorted(order_instance.sections.all(), key=lambda s: s.order_index)

    for section in sections:
        all_items = []

        for item in section.items.all():
            if item.relationship_group_id is None:
                all_items.append(('text', item.order_index, item.id))

        for item in section.drug_items.all():
            if item.relationship_group_id is None:
                all_items.append(('drug', item.order_index, item.id))

        for group in sorted(section.relationship_groups.all(), key=lambda g: g.order_index):
            for item in group.text_items.all():
                all_items.append(('text', item.order_index, item.id))
            for item in group.drug_items.all():
                all_items.append(('drug', item.order_index, item.id))

        all_items.sort(key=lambda x: x[1])

        for item_type, _, item_id in all_items:
            numbering[(item_type, item_id)] = counter
            counter += 1

    return numbering


def collect_section_all_conditions(section):
    """
    اتحاد منحصربه‌فرد تمام شروط مرتبط با آیتم‌های متنی و دارویی یک سکشن
    (هم آیتم‌های مستقل و هم آیتم‌های داخل گروه‌های منطقی).

    نسخه‌ی بهینه‌ی property قبلی `OrderSection.all_conditions`:
      - بدون پرینت‌های دیباگ
      - بدون کوئری اضافه؛ کاملاً روی داده‌های prefetch‌شده (section.items.all(),
        section.drug_items.all()) کار می‌کند چون این querysetها همان روابطی
        هستند که در views.py با Prefetch('items', ...prefetch_related('conditions'))
        و Prefetch('drug_items', ...prefetch_related('conditions')) بارگذاری شده‌اند.
      - خروجی به ترتیب order_index مرتب می‌شود (همان رفتار قبلی).
    """
    conditions_by_id = {}

    for item in section.items.all():
        for condition in item.conditions.all():
            conditions_by_id[condition.id] = condition

    for drug_item in section.drug_items.all():
        for condition in drug_item.conditions.all():
            conditions_by_id[condition.id] = condition

    return sorted(conditions_by_id.values(), key=lambda c: c.order_index)


# ========== CATEGORY SERIALIZER ========== #
class OrderCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionCategory
        fields = ['id', 'title', 'slug', 'color_code']


# ========== ORDER LIST SERIALIZER ========== #
class OrderListSerializer(serializers.ModelSerializer):
    category = OrderCategorySerializer(read_only=True)

    url_base = serializers.SerializerMethodField()
    url_sections = serializers.SerializerMethodField()
    url_disposition = serializers.SerializerMethodField()
    url_dynamic_fields = serializers.SerializerMethodField()
    url_media = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'name', 'slug', 'color',
            'access_level',
            'category',
            'url_base', 'url_sections', 'url_disposition',
            'url_dynamic_fields', 'url_media',
        ]

    def _build_url(self, obj, url_name):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(
                reverse(f'api:v1:ordering_api:{url_name}', kwargs={'slug': obj.slug})
            )
        return None

    def get_url_base(self, obj):
        return self._build_url(obj, 'order-base')

    def get_url_sections(self, obj):
        return self._build_url(obj, 'order-sections')

    def get_url_disposition(self, obj):
        return self._build_url(obj, 'order-disposition')

    def get_url_dynamic_fields(self, obj):
        return self._build_url(obj, 'order-dynamic-fields')

    def get_url_media(self, obj):
        return self._build_url(obj, 'order-media')


# ========== CONDITION SERIALIZER ========== #
class ConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Condition
        fields = ['id', 'text', 'order_index']


# ========== DRUG SERIALIZER ========== #
class DrugSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drug
        fields = ['id', 'title', 'code']


# ========== ORDER ALIAS SERIALIZER ========== #
class OrderAliasSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderAlias
        fields = ['id', 'name', 'is_primary']


# ========== SHARED MIXIN: ITEM NUMBERING ========== #
class ItemNumberMixin(serializers.Serializer):
    """
    Mixin مشترک برای سریالایزرهای SectionItem و DrugSectionItem.
    هر دو نیاز به یک فیلد محاسبه‌شده‌ی `item_number` دارند که از
    context['item_numbering'] (خروجی build_item_numbering) خوانده می‌شود.

    زیرکلاس باید `numbering_item_type` را برابر 'text' یا 'drug' تعریف کند.
    """
    item_number = serializers.SerializerMethodField()
    numbering_item_type = None  # باید در زیرکلاس override شود

    def get_item_number(self, obj):
        numbering = self.context.get('item_numbering', {})
        return numbering.get((self.numbering_item_type, obj.id))


# ========== SECTION ITEM SERIALIZERS ========== #
class SectionItemSerializer(ItemNumberMixin, serializers.ModelSerializer):
    numbering_item_type = 'text'
    conditions = ConditionSerializer(many=True, read_only=True)

    class Meta:
        model = SectionItem
        fields = ['id', 'item_number', 'text', 'notes', 'order_index', 'conditions']


class DrugSectionItemSerializer(ItemNumberMixin, serializers.ModelSerializer):
    numbering_item_type = 'drug'
    drug = DrugSerializer(read_only=True)
    conditions = ConditionSerializer(many=True, read_only=True)

    class Meta:
        model = DrugSectionItem
        fields = ['id', 'item_number', 'drug', 'notes', 'order_index', 'conditions']


# ========== ITEM RELATIONSHIP GROUP SERIALIZER ========== #
class ItemRelationshipGroupSerializer(serializers.ModelSerializer):
    text_items = SectionItemSerializer(many=True, read_only=True)
    drug_items = DrugSectionItemSerializer(many=True, read_only=True)

    class Meta:
        model = ItemRelationshipGroup
        fields = ['id', 'operator', 'order_index', 'text_items', 'drug_items']


# ========== ORDER SECTION SERIALIZER ========== #
class OrderSectionSerializer(serializers.ModelSerializer):
    relationship_groups = serializers.SerializerMethodField()
    ungrouped_items = serializers.SerializerMethodField()
    ungrouped_drug_items = serializers.SerializerMethodField()
    all_conditions = serializers.SerializerMethodField()

    class Meta:
        model = OrderSection
        fields = [
            'id', 'title', 'notes', 'is_drug_section', 'order_index', 'color',
            'relationship_groups', 'ungrouped_items', 'ungrouped_drug_items', 'all_conditions'
        ]

    def get_relationship_groups(self, obj):
        groups = sorted(obj.relationship_groups.all(), key=lambda g: g.order_index)
        return ItemRelationshipGroupSerializer(groups, many=True, context=self.context).data

    def get_ungrouped_items(self, obj):
        ungrouped = [i for i in obj.items.all() if i.relationship_group_id is None]
        return SectionItemSerializer(ungrouped, many=True, context=self.context).data

    def get_ungrouped_drug_items(self, obj):
        ungrouped = [i for i in obj.drug_items.all() if i.relationship_group_id is None]
        return DrugSectionItemSerializer(ungrouped, many=True, context=self.context).data

    def get_all_conditions(self, obj):
        conditions = collect_section_all_conditions(obj)
        return ConditionSerializer(conditions, many=True, context=self.context).data


# ========== EMERGENCY NODE SERIALIZER ========== #
class EmergencyNodeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = EmergencyNode
        fields = [
            'id', 'title', 'content', 'order_index',
            'color', 'is_root', 'children'
        ]

    def get_children(self, obj):
        children = obj.children.all()
        return EmergencyNodeSerializer(children, many=True, context=self.context).data


# ========== EMERGENCY DISPOSITION SERIALIZER ========== #
class EmergencyDispositionSerializer(serializers.ModelSerializer):
    nodes = serializers.SerializerMethodField()

    class Meta:
        model = EmergencyDisposition
        fields = ['id', 'title', 'color', 'notes', 'nodes']

    def get_nodes(self, obj):
        root_nodes = [n for n in obj.nodes.all() if n.parent_id is None]
        return EmergencyNodeSerializer(root_nodes, many=True, context=self.context).data


# ========== DYNAMIC FIELD NODE SERIALIZER ========== #
class DynamicFieldNodeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = DynamicFieldNode
        fields = [
            'id', 'title', 'content', 'order_index',
            'color', 'is_root', 'children'
        ]

    def get_children(self, obj):
        children = obj.children.all()
        return DynamicFieldNodeSerializer(children, many=True, context=self.context).data


# ========== DYNAMIC FIELD GROUP SERIALIZER ========== #
class DynamicFieldGroupSerializer(serializers.ModelSerializer):
    nodes = serializers.SerializerMethodField()

    class Meta:
        model = DynamicFieldGroup
        fields = ['id', 'title', 'order_index', 'color', 'notes', 'nodes']

    def get_nodes(self, obj):
        root_nodes = [n for n in obj.nodes.all() if n.parent_id is None]
        return DynamicFieldNodeSerializer(root_nodes, many=True, context=self.context).data


# ========== ORDER IMAGE SERIALIZER ========== #
class OrderImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderImage
        fields = ['image', 'caption', 'order_index']


# ========== ORDER VIDEO SERIALIZER ========== #
class OrderVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderVideo
        fields = ['video_url', 'title', 'description', 'order_index']


# ========== ORDER BASE SERIALIZER ========== #
class OrderBaseSerializer(serializers.ModelSerializer):
    """سریالایزر پایه برای اطلاعات کلی Order"""
    category = OrderCategorySerializer(read_only=True)
    aliases = serializers.SerializerMethodField()
    primary_name = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'name', 'slug',
            'imp', 'imp_notes',
            'condition', 'condition_notes',
            'diet', 'diet_notes',
            'action', 'action_notes',
            'position', 'position_notes',
            'notes', 'category', 'color',
            'aliases', 'primary_name',
        ]

    def get_aliases(self, obj):
        aliases = sorted(obj.aliases.all(), key=lambda a: a.id)
        return OrderAliasSerializer(aliases, many=True, context=self.context).data

    def get_primary_name(self, obj):
        return obj.get_primary_name()


# ========== ORDER SECTIONS SERIALIZER ========== #
class OrderSectionsSerializer(serializers.ModelSerializer):
    sections = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'slug', 'sections']

    def get_sections(self, obj):
        numbering = build_item_numbering(obj)
        child_context = {**self.context, 'item_numbering': numbering}
        sections = sorted(obj.sections.all(), key=lambda s: s.order_index)
        return OrderSectionSerializer(sections, many=True, context=child_context).data


# ========== ORDER DISPOSITION SERIALIZER ========== #
class OrderDispositionSerializer(serializers.ModelSerializer):
    """سریالایزر برای Emergency Disposition"""
    emergency_disposition = EmergencyDispositionSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'slug', 'emergency_disposition']


# ========== ORDER DYNAMIC FIELDS SERIALIZER ========== #
class OrderDynamicFieldsSerializer(serializers.ModelSerializer):
    """سریالایزر برای Dynamic Field Groups"""
    dynamic_field_groups = DynamicFieldGroupSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'slug', 'dynamic_field_groups']


# ========== ORDER MEDIA SERIALIZER ========== #
class OrderMediaSerializer(serializers.ModelSerializer):
    """سریالایزر برای تصاویر و ویدیوها"""
    images = OrderImageSerializer(many=True, read_only=True)
    videos = OrderVideoSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'slug', 'images', 'videos']
