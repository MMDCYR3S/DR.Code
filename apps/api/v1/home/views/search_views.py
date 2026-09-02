from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from apps.ordering.models import Order
from apps.prescriptions.models import Prescription, PrescriptionCategory
from ..serializers import (
    OrderSearchSerializer,
    PrescriptionSearchSerializer,
)


# مقادیر مجاز برای پارامترهای فیلتر
VALID_RESULT_TYPES = {"all", "orders", "prescriptions"}
VALID_ACCESS_LEVELS = {"all", "free", "premium"}
MAX_RESULTS_PER_TYPE = 50


@extend_schema_view(
    get=extend_schema(
        tags=['Search'],
        summary='جستجوی پیشرفته در اوردرها و نسخه‌ها',
        description=(
            'جستجو بر اساس عبارت + فیلتر پیشرفته شامل نوع نتیجه، دسته‌بندی، '
            'سطح دسترسی اوردر و سطح دسترسی نسخه.\n\n'
            'پارامتر `meta=1` فقط لیست دسته‌بندی‌ها را برمی‌گرداند (برای پر کردن دراپ‌داون).'
        ),
        parameters=[
            OpenApiParameter(name='q', description='عبارت جستجو (اختیاری)', required=False, type=str),
            OpenApiParameter(
                name='type',
                description='نوع نتیجه: all | orders | prescriptions',
                required=False, type=str,
            ),
            OpenApiParameter(
                name='category',
                description='شناسه دسته‌بندی برای فیلتر (اختیاری)',
                required=False, type=int,
            ),
            OpenApiParameter(
                name='order_access',
                description='فیلتر سطح دسترسی اوردر: all | free | premium',
                required=False, type=str,
            ),
            OpenApiParameter(
                name='prescription_access',
                description='فیلتر سطح دسترسی نسخه: all | free | premium',
                required=False, type=str,
            ),
            OpenApiParameter(
                name='meta',
                description='اگر 1 باشد فقط دسته‌بندی‌ها برمی‌گردند (بدون جستجو)',
                required=False, type=bool,
            ),
        ],
    )
)
class SearchAPIView(APIView):
    permission_classes = []

    def get(self, request):
        # ───────────── خواندن و نرمال‌سازی پارامترها ─────────────
        q = request.query_params.get('q', '').strip()
        result_type = request.query_params.get('type', 'all').strip().lower()
        category = request.query_params.get('category', '').strip()
        order_access = request.query_params.get('order_access', 'all').strip().lower()
        prescription_access = request.query_params.get('prescription_access', 'all').strip().lower()
        meta_flag = request.query_params.get('meta', '').strip().lower() in ('1', 'true', 'yes')

        if result_type not in VALID_RESULT_TYPES:
            result_type = 'all'
        if order_access not in VALID_ACCESS_LEVELS:
            order_access = 'all'
        if prescription_access not in VALID_ACCESS_LEVELS:
            prescription_access = 'all'

        # ───────────── لیست دسته‌بندی‌ها (همیشه برگردانده می‌شود) ─────────────
        categories_qs = (
            PrescriptionCategory.objects.all()
            .order_by('title')
            .values('id', 'title', 'slug', 'color_code')
        )

        # حالت meta: فقط دسته‌بندی‌ها را برمی‌گرداند (برای init دراپ‌داون)
        if meta_flag:
            return Response({
                "orders": [],
                "prescriptions": [],
                "categories": list(categories_qs),
            })

        # ───────────── تعیین نیاز به جستجو ─────────────
        filters_active = bool(category) or order_access != 'all' or prescription_access != 'all'
        should_search = bool(q) or filters_active

        orders_data = []
        prescriptions_data = []

        if should_search:
            # ───────────── جستجوی اوردرها ─────────────
            if result_type in ('all', 'orders'):
                orders_qs = Order.objects.filter(is_active=True)
                if q:
                    orders_qs = orders_qs.filter(
                        Q(name__icontains=q) |
                        Q(slug__icontains=q) |
                        Q(imp__icontains=q) |
                        Q(aliases__name__icontains=q)
                    )
                if category:
                    orders_qs = orders_qs.filter(category_id=category)
                if order_access != 'all':
                    orders_qs = orders_qs.filter(access_level__iexact=order_access)
                orders_qs = orders_qs.distinct().order_by('-created_at')[:MAX_RESULTS_PER_TYPE]
                orders_data = OrderSearchSerializer(orders_qs, many=True).data

            # ───────────── جستجوی نسخه‌ها ─────────────
            if result_type in ('all', 'prescriptions'):
                prescriptions_qs = Prescription.objects.filter(is_active=True)
                if q:
                    prescriptions_qs = prescriptions_qs.filter(
                        Q(title__icontains=q) |
                        Q(slug__icontains=q) |
                        Q(aliases__name__icontains=q)
                    )
                if category:
                    prescriptions_qs = prescriptions_qs.filter(category_id=category)
                if prescription_access != 'all':
                    prescriptions_qs = prescriptions_qs.filter(access_level__iexact=prescription_access)
                prescriptions_qs = prescriptions_qs.distinct().order_by('-created_at')[:MAX_RESULTS_PER_TYPE]
                prescriptions_data = PrescriptionSearchSerializer(prescriptions_qs, many=True).data

        return Response({
            "orders": orders_data,
            "prescriptions": prescriptions_data,
            "categories": list(categories_qs),
            "filters": {
                "q": q,
                "type": result_type,
                "category": category,
                "order_access": order_access,
                "prescription_access": prescription_access,
            },
        })
