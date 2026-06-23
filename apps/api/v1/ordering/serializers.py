from django.urls import reverse
from rest_framework import serializers
from apps.ordering.models import (
    Order, OrderSection, Condition, SectionItem, DrugSectionItem,
    EmergencyDisposition, EmergencyNode, DynamicFieldGroup, DynamicFieldNode,
    OrderImage, OrderVideo, ItemRelationshipGroup,
)
from apps.prescriptions.models import Drug, PrescriptionCategory

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
    
    class Meta:
        model = SectionItem
        fields = ['id', 'text', 'notes', 'order_index', 'conditions']

class DrugSectionItemSerializer(serializers.ModelSerializer):
    drug = DrugSerializer(read_only=True)
    conditions = ConditionSerializer(many=True, read_only=True)
    
    class Meta:
        model = DrugSectionItem
        fields = ['id', 'drug', 'notes', 'order_index', 'conditions']

# ========== ITEM RELATIONSHIP GROUP SERIALIZER ========== #
class ItemRelationshipGroupSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای نمایش گروه‌های ارتباطی آیتم‌ها با اپراتور منطقی.
    """
    text_items = SectionItemSerializer(many=True, read_only=True)
    drug_items = DrugSectionItemSerializer(many=True, read_only=True)

    class Meta:
        model = ItemRelationshipGroup
        fields = ['id', 'operator', 'order_index', 'text_items', 'drug_items']

# ========== ORDER SECTION SERIALIZER ========== #
class OrderSectionSerializer(serializers.ModelSerializer):
    relationship_groups = ItemRelationshipGroupSerializer(many=True, read_only=True)
    ungrouped_items = serializers.SerializerMethodField()
    ungrouped_drug_items = serializers.SerializerMethodField()
    
    all_conditions = ConditionSerializer(many=True, read_only=True)
    
    class Meta:
        model = OrderSection
        fields = [
            'id', 'title', 'notes', 'is_drug_section', 'order_index', 'color',
            'relationship_groups',
            'ungrouped_items',
            'ungrouped_drug_items',
            'all_conditions'
        ]

    def get_ungrouped_items(self, obj):
        """
        فقط آیتم‌های متنی را برمی‌گرداند که به هیچ گروهی متصل نیستند.
        """
        ungrouped = [item for item in obj.items.all() if item.relationship_group_id is None]
        return SectionItemSerializer(ungrouped, many=True, context=self.context).data

    def get_ungrouped_drug_items(self, obj):
        """
        فقط آیتم‌های دارویی را برمی‌گرداند که به هیچ گروهی متصل نیستند.
        """
        ungrouped = [item for item in obj.drug_items.all() if item.relationship_group_id is None]
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
    """سریالایزر برای Sections"""
    sections = OrderSectionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'slug', 'sections']

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
