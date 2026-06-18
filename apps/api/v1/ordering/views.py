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
    EmergencyDisposition, EmergencyNode, DynamicFieldGroup, DynamicFieldNode
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
        return Order.objects.filter(
        ).select_related('category').distinct()


# ========== ORDER BASE VIEW ========== #
@extend_schema_view(
    get=extend_schema(
        tags=['Ordering'],
        summary='اطلاعات پایه سفارش',
        description=(
            'اطلاعات پایه‌ی یک سفارش شامل:\n'
            '- نام و تشخیص\n'
            '- وضعیت و رژیم\n'
            '- اقدام و وضعیت قرارگیری\n'
            '- دسته‌بندی و رنگ'
        ),
        parameters=[
            OpenApiParameter(
                name='slug',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='شناسه یکتای سفارش',
            ),
        ],
        responses={
            200: OrderBaseSerializer,
            403: OpenApiResponse(description='دسترسی غیرمجاز'),
            404: OpenApiResponse(description='سفارش یافت نشد'),
        },
    )
)
class OrderBaseView(generics.RetrieveAPIView):
    serializer_class = OrderBaseSerializer
    permission_classes = [IsOrderAccessible, IsTokenJtiActive]
    throttle_classes = [throttling.AnonRateThrottle, throttling.UserRateThrottle]
    lookup_field = 'slug'

    def get_queryset(self):
        return Order.objects.select_related('category')


# ========== ORDER SECTIONS VIEW ========== #
@extend_schema_view(
    get=extend_schema(
        tags=['Ordering'],
        summary='بخش‌ها و آیتم‌های سفارش',
        description=(
            'تمام Section‌های یک سفارش شامل:\n'
            '- آیتم‌های متنی (`items`) با شرط‌های مرتبط\n'
            '- آیتم‌های دارویی (`drug_items`) با اطلاعات دارو و شرط‌ها'
        ),
        parameters=[
            OpenApiParameter(
                name='slug',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='شناسه یکتای سفارش',
            ),
        ],
        responses={
            200: OrderSectionsSerializer,
            403: OpenApiResponse(description='دسترسی غیرمجاز'),
            404: OpenApiResponse(description='سفارش یافت نشد'),
        },
    )
)
class OrderSectionsView(generics.RetrieveAPIView):
    serializer_class = OrderSectionsSerializer
    permission_classes = [IsOrderAccessible, IsTokenJtiActive]
    throttle_classes = [throttling.AnonRateThrottle, throttling.UserRateThrottle]
    lookup_field = 'slug'

    def get_queryset(self):
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
                    )
                )
            )
        )


# ========== ORDER DISPOSITION VIEW ========== #
@extend_schema_view(
    get=extend_schema(
        tags=['Ordering'],
        summary='ساختار درختی تعیین تکلیف اورژانس',
        description=(
            'گره‌های اصلی (root) درخت تعیین تکلیف اورژانس.\n'
            'هر گره می‌تواند دارای فرزندان تودرتو (`children`) باشد.'
        ),
        parameters=[
            OpenApiParameter(
                name='slug',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='شناسه یکتای سفارش',
            ),
        ],
        responses={
            200: OrderDispositionSerializer,
            403: OpenApiResponse(description='دسترسی غیرمجاز'),
            404: OpenApiResponse(description='سفارش یافت نشد'),
        },
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
        summary='فیلدهای پویای سفارش',
        description=(
            'گروه‌های فیلد پویا (`DynamicFieldGroup`) با ساختار درختی.\n'
            'هر گروه شامل گره‌های اصلی و زیرگره‌های تودرتو است.'
        ),
        parameters=[
            OpenApiParameter(
                name='slug',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='شناسه یکتای سفارش',
            ),
        ],
        responses={
            200: OrderDynamicFieldsSerializer,
            403: OpenApiResponse(description='دسترسی غیرمجاز'),
            404: OpenApiResponse(description='سفارش یافت نشد'),
        },
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
        summary='تصاویر و ویدیوهای سفارش',
        description='لیست تصاویر و لینک‌های ویدیویی مرتبط با سفارش.',
        parameters=[
            OpenApiParameter(
                name='slug',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='شناسه یکتای سفارش',
            ),
        ],
        responses={
            200: OrderMediaSerializer,
            403: OpenApiResponse(description='دسترسی غیرمجاز'),
            404: OpenApiResponse(description='سفارش یافت نشد'),
        },
    )
)
class OrderMediaView(generics.RetrieveAPIView):
    serializer_class = OrderMediaSerializer
    permission_classes = [IsOrderAccessible, IsTokenJtiActive]
    throttle_classes = [throttling.AnonRateThrottle, throttling.UserRateThrottle]
    lookup_field = 'slug'

    def get_queryset(self):
        return Order.objects.prefetch_related('images', 'videos')
