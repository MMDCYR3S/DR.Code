from rest_framework import permissions, status, generics
from rest_framework.response import Response
from drf_spectacular.views import extend_schema

from apps.notifications.models import Notification
from ..serializers import UserNotificationSerializer

# ======================================== #
# ======== NOTIFICATION LIST VIEW ======== #
# ======================================== #
@extend_schema(tags=['Notifications'])
class UserNotificationListView(generics.ListAPIView):
    """
    API برای نمایش لیست اعلان‌های کاربر لاگین کرده.
    فقط به درخواست‌های GET پاسخ می‌دهد.
    Endpoint: GET /api/notifications/
    """
    serializer_class = UserNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        فقط اعلان‌های مربوط به کاربر فعلی را برمی‌گرداند.
        اعلان‌های خوانده نشده در ابتدا نمایش داده می‌شوند.
        """
        user = self.request.user
        return Notification.objects.filter(recipient=user).order_by('is_read', '-created_at')
    
    def list(self, request, *args, **kwargs):
        """ ارسال داده ها به همراه پیام های خوانده نشده """
        queryset = self.get_queryset()
        unread_count = queryset.filter(is_read=False).count()
        is_read_count = queryset.filter(is_read=True).count()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'unread_count': unread_count,
            'total_count': is_read_count,
            'notifications': serializer.data
        }, status=status.HTTP_200_OK)

# ================================================== #
# ======== NOTIFICATION MARK AS READ VIEW ======== #
# ================================================== #
@extend_schema(tags=['Notifications'])
class UserNotificationMarkAsReadView(generics.GenericAPIView):
    """
    API برای تعامل با یک اعلان خاص.
    - با متد GET: جزئیات اعلان را برمی‌گرداند و آن را به عنوان خوانده شده علامت می‌زند.
    - با متد POST: اعلان را به عنوان خوانده شده علامت می‌زند (برای سازگاری با درخواست‌های تغییر وضعیت).
    Endpoint: GET, POST /api/notifications/<int:pk>/
    """
    serializer_class = UserNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        برای امنیت، queryset را به اعلان‌های کاربر فعلی محدود می‌کنیم.
        """
        return Notification.objects.filter(recipient=self.request.user)

    def _mark_as_read(self, notification):
        """یک متد کمکی برای جلوگیری از تکرار کد."""
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=['is_read'])
        return notification

    def get(self, request, *args, **kwargs):
        """
        هنگامی که کاربر برای مشاهده جزئیات اعلان (و کلیک روی آن) درخواست GET ارسال می‌کند،
        آن را به عنوان "خوانده شده" علامت می‌زنیم.
        """
        notification = self.get_object()
        notification = self._mark_as_read(notification)
        serializer = self.get_serializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """
        همچنین متد POST را برای علامت‌گذاری به عنوان خوانده شده پشتیبانی می‌کند.
        این یک روش استاندارد REST برای عملیاتی است که وضعیت منبع را تغییر می‌دهد.
        """
        notification = self.get_object()
        notification = self._mark_as_read(notification)
        serializer = self.get_serializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)
        