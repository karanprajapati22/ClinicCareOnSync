from django.urls import path
from . import views

urlpatterns = [

    # ================= COMMON =================
    path('', views.index, name='index'),

    # ================= ADMIN =================
    path('admin_login/', views.admin_login, name='admin_login'),
    path('admin_logout/', views.admin_logout, name='admin_logout'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path('admin_users/', views.admin_user_list, name='admin_users'),
    path('admin_users/edit/<int:id>/', views.admin_user_edit, name='admin_user_edit'),
    path('admin_users/delete/<int:id>/', views.admin_user_delete, name='admin_user_delete'),

    path('departments/', views.admin_departments, name='admin_departments'),
    path('delete-department/<int:id>/', views.delete_department, name='delete_department'),

    path('doctor_category/', views.doctor_category, name='doctor_category'),
    path('edit_category/<int:id>/', views.edit_category, name='edit_category'),
    path('delete_category/<int:id>/', views.delete_category, name='delete_category'),
    
    # path('admin_contacts/', views.admin_contact_messages, name='admin_contacts'),
    path('doctor_feedback/', views.admin_doctor_feedback, name='admin_doctor_feedback'),
    path('add_availability/', views.add_doctor_availability, name='add_doctor_availability'),
    path('availability_list/', views.admin_availability_list, name='admin_availability_list'),
    path('edit_availability/<int:id>/', views.edit_doctor_availability, name='edit_doctor_availability'),
    
    path('admin_appointments/', views.admin_appointments, name='admin_appointments'),
    path('admin_update_appointment/<int:id>/<str:action>/', views.admin_update_appointment_status,name='admin_update_appointment_status'),

    path('admin_contact_messages/', views.admin_contact_list, name='admin_contact_list'),
    path('admin_contact/<int:id>/', views.admin_contact_detail, name='admin_contact_detail'),

    # ================= USER =================
    path('register/', views.register, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('reset_password/', views.reset_password, name='reset_password'),

    path('profile/', views.patient_profile, name='patient_profile'),  
    path('book_appointment/', views.book_appointment, name='book_appointment'),
    path('appointment_status/<int:id>/', views.appointment_status, name='appointment_status'),
    path('my_appointments/', views.my_appointments, name='my_appointments'),
    
    path('contact/', views.contact_suggestion, name='contact_suggestion'),
    path('my_suggestions/', views.patient_suggestions, name='patient_suggestions'),
    path('services/', views.available_services, name='available_services'),

    path('doctor/add-service/', views.add_service, name='add_service'),
    path('doctor/manage-services/', views.manage_services, name='manage_services'),
    path('doctor/edit-service/<int:id>/', views.edit_service, name='edit_service'),
    path('doctor/delete-service/<int:id>/', views.delete_service, name='delete_service'),
    
    # ================= DOCTOR AUTH =================
    path('doctor/register/', views.doctor_register, name='doctor_register'),
    path('doctor/login/', views.doctor_login, name='doctor_login'),
    path('doctor/forgot_password/', views.doctor_forgot_password, name='doctor_forgot_password'),
    path('doctor/verify_otp/', views.doctor_verify_otp, name='doctor_verify_otp'),
    path('doctor/reset_password/', views.doctor_reset_password, name='doctor_reset_password'),
    path('doctor-appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('appointment/update/<int:id>/<str:action>/',views.update_appointment_status,name='update_appointment_status'),
    path('add-suggestion/<int:appointment_id>/',views.add_suggestion,name='add_suggestion'),
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/profile/', views.doctor_profile, name='doctor_profile'),
    path('doctor/patient-feedback/', views.doctor_patient_feedback, name='doctor_patient_feedback'),
    path('doctor/logout/', views.doctor_logout, name='doctor_logout'),

    # # ================= ADMIN: DOCTOR MANAGEMENT =================
    path('doctor_list/', views.doctor_list, name='doctor_list'),
    path('edit_doctor/<int:id>/', views.edit_doctor, name='edit_doctor'),
    path('delete_doctor/<int:id>/', views.delete_doctor, name='delete_doctor'),

    # ================= ADMIN: APPROVAL ACTIONS =================
    path('approve_doctor/<int:id>/', views.approve_doctor, name='approve_doctor'),
    path('reject_doctor/<int:id>/', views.reject_doctor, name='reject_doctor'),

    # ================= RAZORPAY PAYMENT =========================
    path('initiate_payment/<int:appointment_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment_callback/', views.payment_callback, name='payment_callback'),
]
