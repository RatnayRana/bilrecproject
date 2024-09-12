from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("home/", views.home, name="home"),
    path("user/", views.user, name="user"),
    path("uploadbankstatement/", views.uploadBankStatement, name="uploadbankstatement"),
    path("uploaddailyreport/", views.uploaddailyreport, name="uploaddailyreport"),
    path("generateReport/", views.generateReport, name="generateReport"),
    path("startReconcilation/", views.startReconcilation, name="startReconcilation"),
    path('get_account_numbers/', views.get_account_numbers, name='get_account_numbers'),
    path('userpage/', views.userpage, name='userpage'),
    path('loginpage/',views.loginpage,name='loginpage'),

]