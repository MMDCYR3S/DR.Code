from django.urls import reverse
from rest_framework import serializers
from apps.ordering.models import (
    Order, OrderSection, Condition, SectionItem, DrugSectionItem,
    EmergencyDisposition, EmergencyNode, DynamicFieldGroup, DynamicFieldNode,
    OrderImage, OrderVideo, ItemRelationshipGroup,
)
from apps.prescriptions.models import Drug, PrescriptionCategory

def build_item_numbering(order_instance):
    """
    شماره‌گذاری global و پیوسته برای تمام آیتم‌های یک Order.
    کلید: (item_type, item_id) — مقدار: عدد ترتیبی از 1
    item_type: 'text' یا 'drug'
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
            'access_level',          # ← اضافه شد
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

# ========== SECTION ITEM SERIALIZERS ========== #
class SectionItemSerializer(serializers.ModelSerializer):
    conditions = ConditionSerializer(many=True, read_only=True)
    item_number = serializers.SerializerMethodField()

    class Meta:
        model = SectionItem
        fields = ['id', 'item_number', 'text', 'notes', 'order_index', 'conditions']

    def get_item_number(self, obj):
        numbering = self.context.get('item_numbering', {})
        return numbering.get(('text', obj.id))


class DrugSectionItemSerializer(serializers.ModelSerializer):
    drug = DrugSerializer(read_only=True)
    conditions = ConditionSerializer(many=True, read_only=True)
    item_number = serializers.SerializerMethodField()

    class Meta:
        model = DrugSectionItem
        fields = ['id', 'item_number', 'drug', 'notes', 'order_index', 'conditions']

    def get_item_number(self, obj):
        numbering = self.context.get('item_numbering', {})
        return numbering.get(('drug', obj.id))


# ========== ITEM RELATIONSHIP GROUP SERIALIZER ========== #
class ItemRelationshipGroupSerializer(serializers.ModelSerializer):
    text_items = serializers.SerializerMethodField()
    drug_items = serializers.SerializerMethodField()

    class Meta:
        model = ItemRelationshipGroup
        fields = ['id', 'operator', 'order_index', 'text_items', 'drug_items']

    def get_text_items(self, obj):
        return SectionItemSerializer(obj.text_items.all(), many=True, context=self.context).data

    def get_drug_items(self, obj):
        return DrugSectionItemSerializer(obj.drug_items.all(), many=True, context=self.context).data

# ========== ORDER SECTION SERIALIZER ========== #
class OrderSectionSerializer(serializers.ModelSerializer):
    relationship_groups = serializers.SerializerMethodField()
    ungrouped_items = serializers.SerializerMethodField()
    ungrouped_drug_items = serializers.SerializerMethodField()
    all_conditions = ConditionSerializer(many=True, read_only=True)

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
        return EmergencyNodeSerializer(children, many=True).data

# ========== EMERGENCY DISPOSITION SERIALIZER ========== #
class EmergencyDispositionSerializer(serializers.ModelSerializer):
    nodes = serializers.SerializerMethodField()
    
    class Meta:
        model = EmergencyDisposition
        fields = ['id', 'title', 'color', 'notes', 'nodes']
    
    def get_nodes(self, obj):
        # فقط نودهای ریشه را برمی‌گردانیم، بقیه از طریق children بارگذاری می‌شوند
        root_nodes = obj.nodes.filter(parent__isnull=True)
        return EmergencyNodeSerializer(root_nodes, many=True).data

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
        return DynamicFieldNodeSerializer(children, many=True).data

# ========== DYNAMIC FIELD GROUP SERIALIZER ========== #
class DynamicFieldGroupSerializer(serializers.ModelSerializer):
    nodes = serializers.SerializerMethodField()
    
    class Meta:
        model = DynamicFieldGroup
        fields = ['id', 'title', 'order_index', 'color', 'notes', 'nodes']
    
    def get_nodes(self, obj):
        root_nodes = obj.nodes.filter(parent__isnull=True)
        return DynamicFieldNodeSerializer(root_nodes, many=True).data

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
        ]

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
