from django.urls import path
from . import views, utils

urlpatterns = [
    path('', views.create_entry, name='create_entry'),  # Landing page
    path('home', views.create_entry, name='home'),
    path('scan-qr/', views.scan_qr, name='scan-qr'),  # New endpoint for scanning QR
    path('success/', views.entry_success, name='entry_success'),  # Using 'entry_id'
    path('mark_as_scanned/<int:user_entry_id>/', views.mark_as_scanned, name='mark_as_scanned'),  # Using 'entry_id'
    path('qr-scan/<str:qr_data>/', views.qr_scan, name='qr_scan'),
    path('qr-codes/', views.qr_code_list, name='qr_code_list'),
    path('check_qr_status/<int:user_data_id>/', views.check_qr_status, name='check_qr_status'),
    path('temp-add/', views.addEntry, name='temp-add'),
    path('clear-session/', views.clear_session, name='clear-session'),
    path('remove-entry/<int:index>/', views.removeEntry, name='remove-entry'),
    path('export_qr_code/<int:user_entry_id>/', utils.export_qr_code, name='export_qr_code'),
    path('submit-entries/', views.submit_entries, name='submit_entries'),
    path('entrance/', views.entrance, name='entrance'),
    path('mark_as_pending/<int:user_entry_id>/', views.mark_as_pending, name='mark_as_pending'),

]