from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("user/", views.user, name="user"),
    path("uploadbankstatement/", views.uploadBankStatement, name="uploadbankstatement"),
    path("uploaddailyreport/", views.uploaddailyreport, name="uploaddailyreport"),
    path("generateReport/", views.generateReport, name="generateReport"),
    path("startReconcilation/", views.startReconcilation, name="startReconcilation"),
    path('get_account_numbers/', views.get_account_numbers, name='get_account_numbers'),

]