from rest_framework import generics, throttling, permissions
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.filters import OrderingFilter

from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

from apps.accounts.permissions import IsTokenJtiActive
from apps.ordering.models import (
    Order, OrderSection, SectionItem, DrugSectionItem,
    EmergencyDisposition, EmergencyNode, ItemRelationshipGroup, DynamicFieldNode
)
from .serializers import (
    OrderBaseSerializer, OrderSectionsSerializer,
    OrderDispositionSerializer, OrderDynamicFieldsSerializer,
    OrderMediaSerializer, OrderListSerializer
)
from .permissions import IsOrderAccessible


# ========== ORDER LIST VIEW ========== #
@extend_schema_view(
    get=extend_schema(
        tags=['Ordering'],
        summary='لیست سفارش‌ها',
        description='لیست تمام سفارش‌های فعال با قابلیت فیلتر، مرتب‌سازی و صفحه‌بندی.',
        parameters=[
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='مرتب‌سازی: `created_at`, `-created_at`, `name`',
                required=False,
            ),
        ],
        responses={
            200: OrderListSerializer(many=True),
        },
    )
)
class OrderListView(generics.ListAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = Order.objects.select_related('category').distinct()

        access_level = self.request.query_params.get('access_level')
        if access_level in ('FREE', 'PREMIUM'):
            qs = qs.filter(access_level=access_level)

        return qs


# ========== ORDER BASE VIEW ========== #
@extend_schema_view(
    get=extend_schema(
        tags=['Ordering'],
        summary='دریافت اطلاعات اصلی و Clinical Metadata',
        description="""
            اطلاعات کلینیکیِ اصلی هر سفارش را برمی‌گرداند.
            - **ساختار**: شامل فیلدهای اصلی تشخیص (Impression)، وضعیت (Condition)، رژیم (Diet) به همراه یادداشت‌های اختصاصی (Notes) برای هر فیلد.
            - **نکته**: برای نمایش پروفایل کلی سفارش از این بخش استفاده کنید.
        """,
        responses={200: OrderBaseSerializer},
    )
)
class OrderBaseView(generics.RetrieveAPIView):
    serializer_class = OrderBaseSerializer
    permission_classes = [IsOrderAccessible, IsTokenJtiActive]
    throttle_classes = [throttling.AnonRateThrottle, throttling.UserRateThrottle]
    lookup_field = 'slug'

    def get_queryset(self):
        return Order.objects.select_related('category').prefetch_related('aliases')


# ========== ORDER SECTIONS VIEW ========== #
@extend_schema_view(
    get=extend_schema(
        tags=['Ordering'],
        summary='دریافت بخش‌بندی‌های پویا (Sections & Items)',
        description="""
**قلب تپنده سفارش‌دهی — پرکاربردترین و پیچیده‌ترین اندپوینت این سرویس.**

هر Order می‌تواند چند `Section` داشته باشد (مثل Monitoring، Drugs، Imaging).
هر Section از **چهار دسته داده مستقل** تشکیل شده که باید هر کدام جداگانه رندر شوند:

| کلید | نوع | توضیح |
|---|---|---|
| `ungrouped_items` | آرایه SectionItem | آیتم‌های متنی که به هیچ گروه منطقی وصل نیستند |
| `ungrouped_drug_items` | آرایه DrugSectionItem | آیتم‌های دارویی بدون گروه منطقی |
| `relationship_groups` | آرایه ItemRelationshipGroup | گروه‌هایی از آیتم‌ها که با یک اپراتور منطقی (`AND`/`OR`/`THEN`) به هم مرتبط‌اند. هر گروه خودش شامل `text_items` و `drug_items` است |
| `all_conditions` | آرایه Condition | **خلاصهٔ یکتا (union)** تمام شرط‌هایی که در کل این سکشن استفاده شده‌اند (چه در آیتم‌های آزاد، چه داخل گروه‌ها). این فقط برای نمایش سریع/فیلتر است؛ شرط واقعیِ هر آیتم در فیلد `conditions` همان آیتم موجود است |

### شماره‌گذاری سراسری (`item_number`)
هر آیتم متنی یا دارویی، فارغ از اینکه آزاد باشد یا داخل یک گروه، یک `item_number`
**یکتا و پیوسته در کل Order** دارد (نه فقط داخل سکشن). این عدد بر اساس ترتیب واقعی
نمایش محاسبه می‌شود: ابتدا سکشن‌ها طبق `order_index`، سپس داخل هر سکشن آیتم‌های
آزاد و گروه‌ها با هم بر اساس `order_index` ادغام و مرتب می‌شوند، و داخل هر گروه
آیتم‌های متنی قبل از آیتم‌های دارویی شماره می‌گیرند.

⚠️ **نکته مهم فرانت‌اند**: چون خروجی JSON آیتم‌های آزاد را از گروه‌ها جدا کرده،
شماره‌ها لزوماً داخل هر کلید پشت‌سرهم نیستند (مثلاً ممکن است در `ungrouped_items`
شماره‌های ۱ و ۴ باشد چون شمارهٔ ۲ و ۳ به یک گروه در وسط تعلق دارند). برای رندر
صحیح ترتیب واقعی، از `order_index` هر آیتم/گروه برای مرتب‌سازی نهایی در کلاینت
استفاده کنید و از `item_number` فقط به‌عنوان لیبل نمایشی بهره ببرید.

### گروه‌های منطقی
اگر `relationship_groups` غیرخالی باشد، تمام آیتم‌های `text_items` و `drug_items`
آن گروه باید با فاصله‌گذاری بصری و درج اپراتور (`operator`) بین آن‌ها نمایش داده
شوند؛ مثلاً برای `operator: "OR"` بین هر دو آیتم متن «یا» درج شود.

### مثال کامل و دقیقِ ساختار خروجی واقعی:
```json
{
  "id": 12,
  "slug": "acute-mi",
  "sections": [
{
"id": 3,
"title": "Monitoring & Nursing",
"notes": "<p>پایش مداوم علائم حیاتی</p>",
"is_drug_section": false,
"order_index": 0,
"color": "blue",
"ungrouped_items": [
{
"id": 101,
"item_number": 1,
"text": "Check BP q15min",
"notes": "",
"order_index": 0,
"conditions": [
{"id": 5, "text": "if SBP≥90, PR≥60", "order_index": 0}
]
}
],
"ungrouped_drug_items": [],
"relationship_groups": [
{
"id": 7,
"operator": "OR",
"order_index": 1,
"text_items": [
{
"id": 102,
"item_number": 2,
"text": "O2 via nasal cannula 2L/min",
"notes": "",
"order_index": 0,
"conditions": []
},
{
"id": 103,
"item_number": 3,
"text": "O2 via face mask 6L/min",
"notes": "",
"order_index": 1,
"conditions": []
}
],
"drug_items": []
}
],
"all_conditions": [
{"id": 5, "text": "if SBP≥90, PR≥60", "order_index": 0}
]
},
{
"id": 4,
"title": "Drugs",
"notes": "",
"is_drug_section": true,
"order_index": 1,
"color": "red",
"ungrouped_items": [],
"ungrouped_drug_items": [
{
"id": 201,
"item_number": 4,
"drug": {"id": 55, "title": "Aspirin 81mg", "code": "ASA-81"},
"notes": "PO stat, chewable",
"order_index": 0,
"conditions": []
}
],
"relationship_groups": [
{
"id": 8,
"operator": "THEN",
"order_index": 1,
"text_items": [],
"drug_items": [
{
"id": 202,
"item_number": 5,
"drug": {"id": 61, "title": "Nitroglycerin SL", "code": "NTG-SL"},
"notes": "0.4mg sublingual, may repeat q5min x3",
"order_index": 0,
"conditions": [
{"id": 9, "text": "if SBP > 100", "order_index": 0}
]
},
{
"id": 203,
"item_number": 6,
"drug": {"id": 70, "title": "Morphine IV", "code": "MOR-IV"},
"notes": "2-4mg IV push if pain persists",
"order_index": 1,
"conditions": []
}
]
}
],
"all_conditions": [
{"id": 9, "text": "if SBP > 100", "order_index": 0}
]
}
  ]
}
""",
responses={200: OrderSectionsSerializer},
)
)
class OrderSectionsView(generics.RetrieveAPIView):
    serializer_class = OrderSectionsSerializer
    permission_classes = [IsOrderAccessible, IsTokenJtiActive]
    throttle_classes = [throttling.AnonRateThrottle, throttling.UserRateThrottle]
    lookup_field = 'slug'

    def get_queryset(self):
        """
        کوئری بهینه شده با prefetch برای واکشی تمام داده‌های مورد نیاز
        شامل گروه‌های ارتباطی و آیتم‌های داخل آن‌ها.
        """
        return Order.objects.prefetch_related(
            Prefetch(
                'sections',
                queryset=OrderSection.objects.prefetch_related(
                    Prefetch(
                        'items',
                        queryset=SectionItem.objects.prefetch_related('conditions')
                    ),
                    Prefetch(
                        'drug_items',
                        queryset=DrugSectionItem.objects.select_related('drug').prefetch_related('conditions')
                    ),
                    Prefetch(
                        'relationship_groups',
                        queryset=ItemRelationshipGroup.objects.prefetch_related(
                            Prefetch(
                                'text_items',
                                queryset=SectionItem.objects.prefetch_related('conditions')
                            ),
                            Prefetch(
                                'drug_items',
                                queryset=DrugSectionItem.objects.select_related('drug').prefetch_related('conditions')
                            )
                        )
                    )
                )
            )
        )



# ========== ORDER DISPOSITION VIEW ========== #
@extend_schema_view(
    get=extend_schema(
        tags=['Ordering'],
        summary='دریافت ساختار درختی تعیین تکلیف (Disposition)',
        description="""
            ساختار درختیِ گره‌ها (Nodes) برای بخش تعیین تکلیف (مثلاً بستری، ترخیص، انتقال).
            - **نکته**: این ساختار بصورت بازگشتی (Recursive) است؛ هر گره می‌تواند دارای `children` باشد.
            - **کاربرد**: نمایش منوهای درختی برای انتخاب تکلیف نهایی بیمار.
        """,
        responses={200: OrderDispositionSerializer},
    )
)
class OrderDispositionView(generics.RetrieveAPIView):
    serializer_class = OrderDispositionSerializer
    permission_classes = [IsOrderAccessible, IsTokenJtiActive]
    throttle_classes = [throttling.AnonRateThrottle, throttling.UserRateThrottle]
    lookup_field = 'slug'

    def get_queryset(self):
        return Order.objects.prefetch_related(
            Prefetch(
                'emergency_disposition__nodes',
                queryset=EmergencyNode.objects.filter(parent__isnull=True).prefetch_related('children')
            )
        )


# ========== ORDER DYNAMIC FIELDS VIEW ========== #
@extend_schema_view(
    get=extend_schema(
        tags=['Ordering'],
        summary='دریافت فیلدهای پویای سفارشی',
        description="""
            برخی سفارشات ممکن است نیاز به فرم‌های فیلد پویا (Dynamic Field Groups) داشته باشند.
            - **تفاوت**: برخلاف Sectionها، این‌ها برای ساختارهای اطلاعاتی پیچیده‌تر و گره‌بندی‌های اختصاصی طراحی شده‌اند.
        """,
        responses={200: OrderDynamicFieldsSerializer},
    )
)
class OrderDynamicFieldsView(generics.RetrieveAPIView):
    serializer_class = OrderDynamicFieldsSerializer
    permission_classes = [IsOrderAccessible, IsTokenJtiActive]
    throttle_classes = [throttling.AnonRateThrottle, throttling.UserRateThrottle]
    lookup_field = 'slug'

    def get_queryset(self):
        return Order.objects.prefetch_related(
            Prefetch(
                'dynamic_field_groups__nodes',
                queryset=DynamicFieldNode.objects.filter(parent__isnull=True).prefetch_related('children')
            )
        )


# ========== ORDER MEDIA VIEW ========== #
@extend_schema_view(
    get=extend_schema(
        tags=['Ordering'],
        summary='دریافت محتوای آموزشی (تصاویر و ویدیوها)',
        description="""
            منابع کمکی برای Order.
            - **Images**: آرایه‌ای از تصاویر به همراه کپشن و ترتیب نمایش.
            - **Videos**: لینک‌های Embed ویدیو (مانند آپارات یا یوتیوب) برای آموزش‌های ویدیویی.
        """,
        responses={200: OrderMediaSerializer},
    )
)
class OrderMediaView(generics.RetrieveAPIView):
    serializer_class = OrderMediaSerializer
    permission_classes = [IsOrderAccessible, IsTokenJtiActive]
    throttle_classes = [throttling.AnonRateThrottle, throttling.UserRateThrottle]
    lookup_field = 'slug'

    def get_queryset(self):
        return Order.objects.prefetch_related('images', 'videos')
