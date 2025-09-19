from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError
from django.db import transaction

import json
from datetime import datetime

from apps.order.models import DiscountCode
from apps.accounts.permissions import IsTokenJtiActive, HasAdminAccessPermission

# ============================================ #
# ============ DISCOUNT LIST VIEW ============ #
# ============================================ #
class DiscountListView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission,  ListView):
    """
    نمایش لیست کدهای تخفیف
    """
    model = DiscountCode
    template_name = 'dashboard/discounts/discounts.html'
    context_object_name = 'discounts'
    ordering = ['-id']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'مدیریت کدهای تخفیف'
        return context

# ============================================ #
# ============ DISCOUNT CREATE VIEW ============ #
# ============================================ #
@method_decorator(csrf_exempt, name='dispatch')
class DiscountCreateView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """
    ایجاد کد تخفیف جدید
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # اعتبارسنجی داده‌های ورودی
            discount_percent = data.get('discount_percent')
            max_usage = data.get('max_usage', 100)
            
            if not discount_percent or not (1 <= int(discount_percent) <= 100):
                return JsonResponse({
                    'success': False,
                    'message': 'درصد تخفیف باید بین 1 تا 100 باشد'
                }, status=400)
            
            if not max_usage or int(max_usage) < 1:
                return JsonResponse({
                    'success': False,
                    'message': 'حداکثر تعداد استفاده باید بیشتر از 0 باشد'
                }, status=400)
            
            # تبدیل تاریخ‌ها
            start_at = None
            end_at = None
            
            if data.get('start_at'):
                try:
                    start_at = datetime.fromisoformat(data['start_at'].replace('T', ' '))
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'message': 'فرمت تاریخ شروع نامعتبر است'
                    }, status=400)
            
            if data.get('end_at'):
                try:
                    end_at = datetime.fromisoformat(data['end_at'].replace('T', ' '))
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'message': 'فرمت تاریخ پایان نامعتبر است'
                    }, status=400)
            
            # بررسی تاریخ‌ها
            if start_at and end_at and start_at >= end_at:
                return JsonResponse({
                    'success': False,
                    'message': 'تاریخ شروع باید قبل از تاریخ پایان باشد'
                }, status=400)
            
            with transaction.atomic():
                # ایجاد کد تخفیف
                discount_code = DiscountCode.objects.create(
                    title=data.get('title', '').strip(),
                    code=data.get('code', '').strip().upper(),
                    discount_percent=int(discount_percent),
                    start_at=start_at,
                    end_at=end_at,
                    max_usage=int(max_usage),
                    is_active=data.get('is_active', True)
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'کد تخفیف "{discount_code.code}" با موفقیت ایجاد شد',
                    'data': {
                        'id': discount_code.id,
                        'code': discount_code.code
                    }
                })
                
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'خطای داخلی سرور'
            }, status=500)

# ============================================ #
# ============ DISCOUNT UPDATE VIEW============ #
# ============================================ #
@method_decorator(csrf_exempt, name='dispatch')
class DiscountUpdateView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission,  View):
    """
    ویرایش کد تخفیف
    """
    
    def put(self, request, discount_id):
        try:
            discount = get_object_or_404(DiscountCode, id=discount_id)
            data = json.loads(request.body)
            
            # اعتبارسنجی داده‌های ورودی
            discount_percent = data.get('discount_percent')
            max_usage = data.get('max_usage', discount.max_usage)
            
            if not discount_percent or not (1 <= int(discount_percent) <= 100):
                return JsonResponse({
                    'success': False,
                    'message': 'درصد تخفیف باید بین 1 تا 100 باشد'
                }, status=400)
            
            if not max_usage or int(max_usage) < discount.usage_count:
                return JsonResponse({
                    'success': False,
                    'message': f'حداکثر تعداد استفاده نمی‌تواند کمتر از تعداد استفاده فعلی ({discount.usage_count}) باشد'
                }, status=400)
            
            # تبدیل تاریخ‌ها
            start_at = None
            end_at = None
            
            if data.get('start_at'):
                try:
                    start_at = datetime.fromisoformat(data['start_at'].replace('T', ' '))
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'message': 'فرمت تاریخ شروع نامعتبر است'
                    }, status=400)
            
            if data.get('end_at'):
                try:
                    end_at = datetime.fromisoformat(data['end_at'].replace('T', ' '))
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'message': 'فرمت تاریخ پایان نامعتبر است'
                    }, status=400)
            
            # بررسی تاریخ‌ها
            if start_at and end_at and start_at >= end_at:
                return JsonResponse({
                    'success': False,
                    'message': 'تاریخ شروع باید قبل از تاریخ پایان باشد'
                }, status=400)
            
            with transaction.atomic():
                # بروزرسانی کد تخفیف
                discount.title = data.get('title', discount.title).strip()
                
                # فقط اگر کد جدید ارائه شده باشد
                new_code = data.get('code', '').strip().upper()
                if new_code and new_code != discount.code:
                    # بررسی یکتا بودن کد جدید
                    if DiscountCode.objects.filter(code=new_code).exclude(id=discount.id).exists():
                        return JsonResponse({
                            'success': False,
                            'message': 'این کد تخفیف قبلاً استفاده شده است'
                        }, status=400)
                    discount.code = new_code
                
                discount.discount_percent = int(discount_percent)
                discount.start_at = start_at
                discount.end_at = end_at
                discount.max_usage = int(max_usage)
                discount.is_active = data.get('is_active', discount.is_active)
                
                discount.full_clean()
                discount.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'کد تخفیف "{discount.code}" با موفقیت بروزرسانی شد'
                })
                
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'خطای داخلی سرور'
            }, status=500)

# ============================================ #
# ============ DISCOUNT DELETE VIEW ============ #
# ============================================ #
@method_decorator(csrf_exempt, name='dispatch')
class DiscountDeleteView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission,  View):
    """
    حذف کد تخفیف
    """
    
    def delete(self, request, discount_id):
        try:
            discount = get_object_or_404(DiscountCode, id=discount_id)
            
            # بررسی امکان حذف
            if discount.usage_count > 0:
                return JsonResponse({
                    'success': False,
                    'message': 'این کد تخفیف قبلاً استفاده شده و قابل حذف نیست'
                }, status=400)
            
            code = discount.code
            discount.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'کد تخفیف "{code}" با موفقیت حذف شد'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'خطای داخلی سرور'
            }, status=500)
