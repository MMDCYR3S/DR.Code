from django.urls import path
from .. import views

urlpatterns = [
    path('', views.ProfileView.as_view(), name='profile'),
    path('update/', views.UpdateProfileView.as_view(), name='update_profile'),
    path(
        'prescription/save/<str:slug>/', 
        views.PrescriptionSaveToggleView.as_view(), 
        name='prescription-save-toggle'
    ),
    path(
        'saved/', 
        views.SavedPrescriptionListView.as_view(), 
        name='saved-prescriptions-list'
    ),
    
    path(
        'questions/', 
        views.QuestionListAPIView.as_view(), 
        name='questions-prescriptions-list'
    ),
    
]
