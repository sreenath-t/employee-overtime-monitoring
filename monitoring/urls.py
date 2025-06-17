from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('upload/', views.upload_csv, name='upload_csv'),
    path('overtime-records/', views.show_overtime_records, name='show_overtime_records'),
    path('analysis/', views.overtime_analysis, name='overtime_analysis'),
    path('visual-analysis/',views.visual_analysis, name='visual_analysis'),
    path('business_impact/',views.business_impact, name='business_impact'),
]