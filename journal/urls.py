from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('workout/', views.WorkoutDetailView.as_view(), name='workout_detail'),
    path('request-info/', views.request_info, name='request_info'),
    path('plan/generate/', views.GeneratePlanView.as_view(), name='plan_generate'),
    path('assistant/', views.AssistantView.as_view(), name='ai_assistant'),
    path('assistant/ask/', views.AssistantAskView.as_view(), name='ai_ask'),
    path('assistant/clear/', views.AssistantClearView.as_view(), name='ai_clear'),
]
