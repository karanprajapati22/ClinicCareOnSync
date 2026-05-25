from django.contrib import admin
from .models import *


# Register your models here.
class register_user(admin.ModelAdmin):
    list_display = ('username','user', 'mobile', 'address', 'city', 'state', 'pincode')
    search_fields=('username','email')


class department(admin.ModelAdmin):
    list_display = ('department_name',)
    search_fields=('department_name',)


class category(admin.ModelAdmin):
    list_display = ('category_name', 'department')
    search_fields = ('category_name', 'department__department_name')  
    
class doctor_register(admin.ModelAdmin):
    list_display = ('doctor_name', 'email','mobile', 'department', 'category', 'qualification', 'experience', 'photo', 'certificate')
    search_fields = ('doctor_name', 'email', 'department__department_name', 'category__category_name')
    list_filter = ('department', 'category')

class appointment(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'appointment_date', 'appointment_time', 'status', 'created_at')
    search_fields = ('patient__username', 'doctor__doctor_name', 'appointment_date', 'status')
    list_filter = ('status', 'appointment_date')
    
class contact_admin(admin.ModelAdmin):
    list_display = ('name', 'email', 'message', 'created_at','doctor')
    search_fields = ('name', 'email', 'message')
    list_filter = ('created_at',)
    
class checkup(admin.ModelAdmin):
    list_display = ('appointment', 'suggestion', 'created_at')
    search_fields = ('appointment__patient__username', 'appointment__doctor__doctor_name', 'suggestion')
    list_filter = ('created_at',)

class service_admin(admin.ModelAdmin):
    list_display = ('service_name', 'doctor', 'icon_class')
    search_fields = ('service_name', 'doctor__doctor_name')
    list_filter = ('doctor',)

admin.site.register(registration,register_user)
admin.site.register(Department,department)
admin.site.register(DoctorCategory,category)
admin.site.register(DoctorRegister,doctor_register)
admin.site.register(Appointment,appointment)
admin.site.register(Contact,contact_admin)
admin.site.register(Checkup,checkup)
admin.site.register(DoctorAvailability)
admin.site.register(Service,service_admin)