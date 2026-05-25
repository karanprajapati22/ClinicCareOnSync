from django.db import models
from django.contrib.auth.models import User   # CHANGED

#registration 
class registration(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # CHANGED

    username = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15)
    address = models.TextField()
    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)

    def __str__(self):
        return self.email

#department
class Department(models.Model):
    department_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.department_name

#category
class DoctorCategory(models.Model):
    category_name = models.CharField(max_length=100, unique=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='categories'
    )

    def __str__(self):
        return self.category_name
    
#doctor registration
class DoctorRegister(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    doctor_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15)

    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    category = models.ForeignKey(DoctorCategory, on_delete=models.CASCADE)

    qualification = models.CharField(max_length=100)
    experience = models.IntegerField()

    photo = models.ImageField(upload_to='doctor_photos/')
    certificate = models.FileField(upload_to='doctor_certificates/', null=True, blank=True)

    is_approved = models.BooleanField(default=False)   # ✅ NEW

    def __str__(self):
        return f"Dr. {self.doctor_name}"

#appointment
class Appointment(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )

    patient = models.ForeignKey(
        registration,
        on_delete=models.CASCADE
    )

    doctor = models.ForeignKey(
        DoctorRegister,
        on_delete=models.CASCADE
    )

    appointment_date = models.DateField()
    appointment_time = models.TimeField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # Razorpay payment fields
    is_paid = models.BooleanField(default=False)
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.patient.username} - {self.doctor}"

#-----------------
class Contact(models.Model):
    
    doctor = models.ForeignKey(
        DoctorRegister,
        on_delete=models.CASCADE,
        related_name='feedbacks',
        null=True,
        blank=True
    )

    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.doctor.doctor_name if self.doctor else 'General'}"

    
#-----------------DOCTOR CHECKUP SUGGESTION MODEL -----------------
    # CHECKUP / SUGGESTION MODEL
class Checkup(models.Model):
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name="checkup"
    )

    doctor = models.ForeignKey(
        DoctorRegister,
        on_delete=models.CASCADE
    )

    patient = models.ForeignKey(
        registration,
        on_delete=models.CASCADE
    )

    suggestion = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Checkup - {self.patient.username}"

#------------------
class DoctorAvailability(models.Model):

    doctor = models.ForeignKey(
        DoctorRegister,
        on_delete=models.CASCADE,
        related_name="availabilities"
    )

    available_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.doctor.doctor_name} - {self.available_date}"
    
#-----------------SERVICE MODEL-----------------

class Service(models.Model):
    doctor = models.ForeignKey(DoctorRegister, on_delete=models.CASCADE, null=True, blank=True)
    service_name = models.CharField(max_length=100)
    short_description = models.TextField()
    service_image = models.ImageField(upload_to='service_images/', blank=True, null=True)
    icon_class = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.service_name