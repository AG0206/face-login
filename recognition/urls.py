from django.urls import path
from . import views

app_name = 'recognition'
urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.user_login, name='login'),
    path('face-login/', views.face_login, name='face_login'),

    path('logout/', views.user_logout, name='logout'),
    path('register/', views.user_register, name='register'),
    path('franchise-register/', views.franchise_owner_register, name='franchise_owner_register'),
    path('super-admin/dashboard/', views.super_admin_dashboard, name='super_admin_dashboard'),
    path('super-admin/reset-password/<int:user_id>/', views.reset_user_password, name='reset_user_password'),
    path('franchise-owner/dashboard/', views.franchise_owner_dashboard, name='franchise_owner_dashboard'),
    path('franchise-owner/edit/', views.franchise_edit, name='franchise_edit'),
    path('franchise-owner/manage-users/', views.franchise_manage_users, name='franchise_manage_users'),
    path('franchise-owner/user/<int:user_id>/history/', views.user_book_history, name='user_book_history'),
    path('franchise-owner/transactions/', views.franchise_transactions, name='franchise_transactions'),
    path('user/dashboard/', views.user_dashboard, name='user_dashboard'),
    path('books/', views.book_list, name='book_list'),
    path('books/create/', views.book_create, name='book_create'),
    path('books/<int:book_id>/edit/', views.book_edit, name='book_edit'),
    path('books/<int:book_id>/delete/', views.book_delete, name='book_delete'),
    path('books/issue/', views.book_issue, name='book_issue'),
    path('books/<int:issue_id>/return/', views.book_return, name='book_return'),
    path('detect/', views.detect_faces_page, name='detect_faces_page'),
    path('detect/api/', views.detect_faces, name='detect_faces'),
    path('detect/upload/', views.upload_and_detect, name='upload_and_detect'),
    path('records/', views.face_records_list, name='face_records_list'),
    path('user/update-face/', views.update_user_face, name='update_user_face'),
]