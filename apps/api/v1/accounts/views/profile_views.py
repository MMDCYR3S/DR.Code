from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from apps.accounts.models import Profile, AuthStatusChoices
from ..serializers import ProfileSerializer, UpdateProfileSerializer

from PIL import Image

import logging

from .base_view import BaseAPIView

User = get_user_model()
logger = logging.getLogger(__name__)


# ============ PROFILE VIEWS ============ #
class ProfileView(RetrieveAPIView, BaseAPIView):
    """
    نمایش اطلاعات پروفایل کاربر
    """
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """دریافت پروفایل کاربر فعلی"""
        return self.request.user.profile

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return self.handle_exception(e)

# ============= UPDATE PROFILE VIEWS ============= #
class UpdateProfileView(BaseAPIView):
    """
    بروزرسانی اطلاعات پایه پروفایل
    
    فیلدهای قابل ویرایش:
    - نام و نام خانوادگی
    - ایمیل
    - عکس پروفایل
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UpdateProfileSerializer

    def patch(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                user = request.user
                
                # دریافت اطلاعات قبلی برای مقایسه
                old_data = {
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'profile_image': user.profile.profile_image.name if user.profile.profile_image else None
                }
                
                serializer = self.serializer_class(
                    instance=user,
                    data=request.data,
                    partial=True,  # اجازه بروزرسانی جزئی
                    context={'request': request}
                )
                
                if serializer.is_valid():
                    # بروزرسانی اطلاعات
                    updated_user = serializer.save()
                    
                    # تشخیص فیلدهای تغییر یافته
                    changed_fields = []
                    new_data = {
                        'first_name': updated_user.first_name,
                        'last_name': updated_user.last_name,
                        'email': updated_user.email,
                        'profile_image': updated_user.profile.profile_image.name if updated_user.profile.profile_image else None
                    }
                    
                    for field, old_value in old_data.items():
                        new_value = new_data[field]
                        if old_value != new_value:
                            changed_fields.append(field)
                    
                    # پردازش تصویر پروفایل در صورت آپلود جدید
                    if 'profile_image' in changed_fields and updated_user.profile.profile_image:
                        self._process_profile_image(updated_user.profile)
                    
                    # حذف تصویر قدیمی در صورت تغییر
                    if ('profile_image' in changed_fields and 
                        old_data['profile_image'] and 
                        old_data['profile_image'] != new_data['profile_image']):
                        self._delete_old_image(old_data['profile_image'])
                    
                    logger.info(f"پروفایل بروزرسانی شد: {user.phone_number} - فیلدها: {changed_fields}")
                    
                    # آماده‌سازی پاسخ
                    response_data = {
                        'success': True,
                        'message': 'اطلاعات با موفقیت بروزرسانی شد.',
                        'data': {
                            'updated_fields': changed_fields,
                            'updated_count': len(changed_fields),
                            'user': {
                                'id': updated_user.id,
                                'first_name': updated_user.first_name,
                                'last_name': updated_user.last_name,
                                'full_name': updated_user.full_name,
                                'email': updated_user.email,
                                'profile_image': updated_user.profile.profile_image.url if updated_user.profile.profile_image else None
                            },
                            'updated_at': timezone.now().isoformat()
                        }
                    }
                    
                    return Response(response_data, status=status.HTTP_200_OK)
                
                # خطاهای اعتبارسنجی
                error_messages = []
                for field, errors in serializer.errors.items():
                    if isinstance(errors, list):
                        error_messages.extend([f"{field}: {error}" for error in errors])
                    else:
                        error_messages.append(f"{field}: {str(errors)}")
                
                return Response({
                    'success': False,
                    'message': 'خطا در اطلاعات ارسالی',
                    'errors': serializer.errors,
                    'error_details': error_messages
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return self.handle_exception(e)

    def _process_profile_image(self, profile):
        """
        پردازش و بهینه‌سازی تصویر پروفایل
        """
        try:
            if not profile.profile_image:
                return
            
            # باز کردن تصویر
            image = Image.open(profile.profile_image)
            
            # تبدیل به RGB در صورت نیاز
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            # تغییر اندازه در صورت نیاز (حداکثر 800x800)
            max_size = (800, 800)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # ذخیره تصویر بهینه‌شده
            from io import BytesIO
            output = BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            # جایگزینی فایل قدیمی
            file_name = f"profile_images/{profile.user.id}_{timezone.now().timestamp()}.jpg"
            
            # حذف فایل قدیمی
            if profile.profile_image:
                old_file = profile.profile_image.name
                profile.profile_image.delete(save=False)
            
            # ذخیره فایل جدید
            profile.profile_image.save(
                file_name,
                ContentFile(output.getvalue()),
                save=True
            )
            
            logger.info(f"تصویر پروفایل بهینه‌سازی شد: {profile.user.phone_number}")
            
        except Exception as e:
            logger.error(f"خطا در پردازش تصویر پروفایل: {str(e)}")
    
    def _delete_old_image(self, old_image_path):
        """
        حذف تصویر قدیمی
        """
        try:
            if old_image_path and default_storage.exists(old_image_path):
                default_storage.delete(old_image_path)
                logger.info(f"تصویر قدیمی حذف شد: {old_image_path}")
        except Exception as e:
            logger.error(f"خطا در حذف تصویر قدیمی: {str(e)}")

    def get(self, request, *args, **kwargs):
        """
        دریافت اطلاعات فعلی پروفایل برای نمایش در فرم
        """
        try:
            user = request.user
            profile = user.profile
            
            return Response({
                'success': True,
                'data': {
                    'user': {
                        'id': user.id,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'full_name': user.full_name,
                        'phone_number': user.phone_number,
                        'email': user.email,
                        'profile_image': profile.profile_image.url if profile.profile_image else None,
                        'date_joined': user.date_joined.isoformat(),
                        'last_login': user.last_login.isoformat() if user.last_login else None
                    },
                    'profile': {
                        'auth_status': profile.auth_status,
                        'auth_status_display': profile.get_auth_status_display(),
                        'role': profile.role,
                        'role_display': profile.get_role_display(),
                        'medical_code': profile.medical_code,
                        'referral_code': profile.referral_code
                    }
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return self.handle_exception(e)