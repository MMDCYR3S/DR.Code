// --- بررسی JTI بلافاصله بعد از بارگذاری اسکریپت ---
(async function immediateJtiCheck() {
  const accessToken = localStorage.getItem('drcode_access_token');
  const localJTI = localStorage.getItem('drcode_user_jti');

  // اگر هیچ‌کدام وجود ندارد، نیازی نیست ادامه بدهد
  if (!accessToken || !localJTI) return;

  try {
    const response = await fetch('/api/v1/accounts/login-status/', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Accept': 'application/json',
      },
      cache: 'no-store'
    });

    // اگر توکن منقضی شده یا معتبر نیست
    if (![200, 201].includes(response.status)) {
      clearLocalAuth();
      return;
    }

    const data = await response.json();
    const serverJTI = data?.data?.user?.active_jti;

    // مقایسه JTI سرور و لوکال
    if (serverJTI && serverJTI !== localJTI) {
      clearLocalAuth();
    }

  } catch (err) {
    console.error('Immediate JTI check error:', err);
    clearLocalAuth();
  }
})();

// تابع حذف و هدایت
function clearLocalAuth() {
  localStorage.removeItem('drcode_access_token');
  localStorage.removeItem('drcode_refresh_token');
  localStorage.removeItem('drcode_user_jti');
  localStorage.removeItem('drcode_user_data');
  localStorage.removeItem('drcode_user_profile');
  localStorage.removeItem('medical_code');
}
