# ===== Django core =====
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden   # ✅ ADD THIS
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
import razorpay

# ===== Email & settings =====
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from xhtml2pdf import pisa
from io import BytesIO

# ===== Utilities =====
import re
import random

# ===== Project models & forms =====
from .models import DoctorRegister, Department, DoctorCategory
from .forms import *


# ================= HELPERS =================

def send_appointment_invoice_email(appointment):
    """
    Sends a premium HTML email and a PDF invoice to the patient after appointment approval.
    """
    subject = f"Appointment Confirmed & Invoice - #APT-{appointment.id}"
    
    context = {
        'patient_name': appointment.patient.username,
        'doctor_name': str(appointment.doctor),
        'appointment_id': appointment.id,
        'appointment_date': appointment.appointment_date,
        'appointment_time': appointment.appointment_time,
        'is_paid': appointment.is_paid,
        'payment_id': appointment.razorpay_payment_id,
        'amount': settings.APPOINTMENT_FEE,
        'today': timezone.now().date(),
    }
    
    # 1. Render HTML for Email
    html_content = render_to_string('invoice_email.html', context)
    text_content = strip_tags(html_content)
    
    # 2. Generate PDF Invoice
    pdf_html = render_to_string('invoice_pdf.html', context)
    pdf_file = BytesIO()
    pisa_status = pisa.CreatePDF(pdf_html, dest=pdf_file)
    
    # 3. Send Email with Attachment
    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [appointment.patient.email]
    )
    email.attach_alternative(html_content, "text/html")
    
    if not pisa_status.err:
        email.attach(f'Invoice_APT_{appointment.id}.pdf', pdf_file.getvalue(), 'application/pdf')
    
    try:
        email.send()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


# ================= ADMIN =================

def admin_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            messages.error(request, "Invalid Email or Password")
            return redirect("admin_login")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_staff or user.is_superuser:
                login(request, user)
                return redirect("admin_dashboard")
            else:
                messages.error(request, "You are not authorized as admin")
                return redirect("admin_login")
        else:
            messages.error(request, "Invalid Email or Password")
            return redirect("admin_login")

    return render(request, "admin/admin_login.html")


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import DoctorRegister, registration, Appointment

# ================= ADMIN DASHBOARD =================
@login_required
def admin_dashboard(request):

    # SECURITY CHECK (only admin)
    if not request.user.is_superuser:
        return redirect('admin_login')

    total_doctors = DoctorRegister.objects.count()
    total_patients = registration.objects.count()
    total_appointments = Appointment.objects.count()

    context = {
        'total_doctors': total_doctors,
        'total_patients': total_patients,
        'total_appointments': total_appointments,
    }

    return render(request, 'admin/admin_dashboard.html', context)

@login_required(login_url="admin_login")
def admin_user_list(request):
    users = registration.objects.all().order_by("-id")
    return render(request, "admin/user_list.html", {
        "users": users,
        "total_users": users.count()
    })

@login_required(login_url="admin_login")
def admin_user_edit(request, id):
    user = get_object_or_404(registration, id=id)

    if request.method == "POST":
        user.username = request.POST.get("username")
        user.email = request.POST.get("email")
        user.mobile = request.POST.get("mobile")
        user.address = request.POST.get("address")
        user.save()
        return redirect("admin_users")

    return render(request, "admin/user_edit.html", {"user": user})


@login_required(login_url="admin_login")
def admin_user_delete(request, id):
    registration.objects.get(id=id).delete()
    return redirect("admin_users")

@login_required(login_url="admin_login")
def admin_departments(request):
    if request.method == "POST":
        name = request.POST.get("department_name")
        if name:
            Department.objects.create(department_name=name)

    return render(request, "admin/departments.html", {
        "departments": Department.objects.all().order_by("-id")
    })


@login_required(login_url="admin_login")
def delete_department(request, id):
    Department.objects.get(id=id).delete()
    return redirect("admin_departments")

@login_required(login_url="admin_login")
# def admin_contact_messages(request):
#     contacts = Contact.objects.all().order_by('-created_at')

#     return render(request, "admin/contact_messages.html", {
#         "contacts": contacts,
#         "total_contacts": contacts.count()
#     })

def admin_doctor_feedback(request):

    doctor_id = request.GET.get('doctor')
    date_filter = request.GET.get('date')

    feedbacks = Contact.objects.select_related('doctor').all().order_by('-created_at')

    # Filter by doctor
    if doctor_id:
        feedbacks = feedbacks.filter(doctor_id=doctor_id)

    # Filter by date
    if date_filter:
        feedbacks = feedbacks.filter(created_at__date=date_filter)

    doctors = DoctorRegister.objects.all()

    return render(request, "admin/doctor_feedback.html", {
        "feedbacks": feedbacks,
        "doctors": doctors,
        "selected_doctor": doctor_id,
        "selected_date": date_filter
    })

# ================= ADMIN CONTACT LIST =================
@login_required(login_url="admin_login")
def admin_contact_list(request):
    query = request.GET.get('q')

    contacts = Contact.objects.all().order_by('-created_at')

    if query:
        contacts = contacts.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(message__icontains=query)
        )

    return render(request, 'admin/contact_list.html', {
        'contacts': contacts,
        'query': query
    })


# ================= ADMIN CONTACT DETAIL =================
@login_required(login_url="admin_login")
def admin_contact_detail(request, id):
    contact = Contact.objects.get(id=id)

    return render(request, 'admin/contact_detail.html', {
        'contact': contact
    })

#================= DOCTOR AVAILABILITY MANAGEMENT =================
# ADD AVAILABILITY
@login_required(login_url="admin_login")
def add_doctor_availability(request):

    if request.method == "POST":
        form = DoctorAvailabilityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Availability added successfully.")
            return redirect('admin_availability_list')
    else:
        form = DoctorAvailabilityForm()

    return render(request, 'admin/add_availability.html', {'form': form})


# LIST AVAILABILITY
@login_required(login_url="admin_login")
def admin_availability_list(request):

    availabilities = DoctorAvailability.objects.select_related('doctor').order_by('-available_date')

    return render(request, 'admin/availability_list.html', {
        'availabilities': availabilities
    })


# EDIT AVAILABILITY
@login_required(login_url="admin_login")
def edit_doctor_availability(request, id):

    availability = get_object_or_404(DoctorAvailability, id=id)

    if request.method == "POST":
        form = DoctorAvailabilityForm(request.POST, instance=availability)
        if form.is_valid():
            form.save()
            messages.success(request, "Availability updated successfully.")
            return redirect('admin_availability_list')
    else:
        form = DoctorAvailabilityForm(instance=availability)

    return render(request, 'admin/add_availability.html', {'form': form})


# ================= ADMIN APPOINTMENT LIST =================
@login_required(login_url="admin_login")
def admin_appointments(request):

    # Only admin access
    if not request.user.is_superuser:
        return redirect('login')

    appointments = Appointment.objects.select_related(
        'doctor', 'patient'
    ).order_by('-created_at')

    return render(request, 'admin/admin_appointments.html', {
        'appointments': appointments
    })


# ================= UPDATE STATUS =================
@login_required(login_url="admin_login")
def admin_update_appointment_status(request, id, action):

    if not request.user.is_superuser:
        return redirect('login')

    appointment = get_object_or_404(Appointment, id=id)

    if action == "approve":
        # Check if slot is already booked (Approved)
        if Appointment.objects.filter(
            doctor=appointment.doctor,
            appointment_date=appointment.appointment_date,
            appointment_time=appointment.appointment_time,
            status='Approved'
        ).exclude(id=id).exists():
            messages.error(request, "This slot is already booked by another approved appointment.")
            return redirect('admin_appointments')

        appointment.status = "Approved"
        
        # Auto-reject other pending appointments for same slot
        Appointment.objects.filter(
            doctor=appointment.doctor,
            appointment_date=appointment.appointment_date,
            appointment_time=appointment.appointment_time,
            status='Pending'
        ).exclude(id=id).update(status='Rejected')

        messages.success(request, "Appointment approved successfully. Patient can now pay the fee.")
    elif action == "reject":
        appointment.status = "Rejected"
        messages.error(request, "Appointment rejected.")

    appointment.save()

    return redirect('admin_appointments')


def admin_logout(request):
    logout(request)
    return redirect("admin_login")


# ================= USER =================
def register(request):
    if request.method == "POST":

        username = request.POST['username']   # real name
        email = request.POST['email']
        password = request.POST['password']
        mobile = request.POST['mobile']
        address = request.POST['address']
        state = request.POST['state']
        city = request.POST['city']
        pincode = request.POST['pincode']

        # PASSWORD VALIDATION
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long")
            return render(request, "register.html")

        # EMAIL UNIQUE CHECK (IMPORTANT)
        if User.objects.filter(username=email).exists():
            messages.error(request, "Email already registered")
            return render(request, "register.html")

        # ✅ CREATE USER (EMAIL AS USERNAME)
        user = User.objects.create_user(
            username=email,   # ✅ ALWAYS UNIQUE
            email=email,
            password=password
        )

        # CREATE REGISTRATION PROFILE
        registration.objects.create(
            user=user,
            username=username,   # real name
            email=email,
            mobile=mobile,
            address=address,
            state=state,
            city=city,
            pincode=pincode
        )

        messages.success(request, "Registration successful. Please login.")

        send_mail(
            subject="Welcome to Clinic Care On Sync",
            message=f"Hello {username}, welcome to Clinic Care On Sync!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return redirect('login')

    return render(request, "register.html")


from django.contrib.auth import authenticate, login
from django.contrib import messages
def login_user(request):
    if request.method == "POST":

        email = request.POST['email']
        password = request.POST['password']

        # EMAIL USED AS USERNAME
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, "Invalid Email or Password")

    return render(request, "login.html")


# protected patient profile view

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import registration

# ================= PATIENT PROFILE UPDATE =================
@login_required(login_url='login')
def patient_profile(request):

    try:
        user_profile = registration.objects.get(user=request.user)
    except registration.DoesNotExist:
        return redirect('login')

    if request.method == "POST":
        user_profile.username = request.POST.get('username')
        user_profile.mobile = request.POST.get('mobile')
        user_profile.address = request.POST.get('address')
        user_profile.city = request.POST.get('city')
        user_profile.state = request.POST.get('state')
        user_profile.pincode = request.POST.get('pincode')

        user_profile.save()
        messages.success(request, "Profile updated successfully!")

        return redirect('patient_profile')

    return render(request, 'profile.html', {
        'profile': user_profile
    })

#======== forgot password view ================
def forgot_password(request):
    if request.method == "POST":
        email = request.POST['email']

        # check email exists
        if not User.objects.filter(email=email).exists():
            messages.error(request, "Email not registered")
            return render(request, "forgot_password.html")

        # generate 6-digit OTP
        otp = random.randint(100000, 999999)

        # store OTP in session
        request.session['reset_email'] = email
        request.session['reset_otp'] = str(otp)

        # ✅ SEND OTP TO EMAIL
        send_mail(
            subject="Password Reset OTP",
            message=f"Your password reset OTP is {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        messages.success(request, "OTP sent to your email")
        return redirect('verify_otp')

    return render(request, "forgot_password.html")

# ======== verify otp view ================
def verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST['otp']
        stored_otp = request.session.get('reset_otp')

        if stored_otp and entered_otp == stored_otp:
            messages.success(request, "OTP verified successfully")
            return redirect('reset_password')
        else:
            messages.error(request, "Invalid OTP")

    return render(request, "verify_otp.html")

# ======== reset password view ================
def reset_password(request):
    if request.method == "POST":
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        # password length validation
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters")
            return render(request, "reset_password.html")

        # confirm password check
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, "reset_password.html")

        email = request.session.get('reset_email')

        if not email:
            messages.error(request, "Session expired. Try again.")
            return redirect('forgot_password')

        user = User.objects.get(email=email)
        user.password = make_password(password)
        user.save()

        # clear session data
        request.session.flush()

        messages.success(request, "Password reset successful. Please login.")
        return redirect('login')

    return render(request, "reset_password.html")

# APPOINTMENT BOOKING =========================
# ================= APPOINTMENT BOOKING =========================

@login_required
def book_appointment(request):

    # 🚫 Prevent doctor from accessing patient booking
    if DoctorRegister.objects.filter(user=request.user).exists():
        return HttpResponseForbidden("Doctors cannot book appointments.")

    # ✅ Safe patient fetch (no crash)
    patient = registration.objects.filter(user=request.user).first()

    if not patient:
        return HttpResponseForbidden("Patient profile not found.")

    appointments = Appointment.objects.filter(
        patient=patient
    ).order_by('-created_at')

    if request.method == 'POST':
        form = AppointmentForm(request.POST)

        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = patient
            appointment.status = 'Pending'

            # Date validation (no past date)
            if appointment.appointment_date < timezone.now().date():
                form.add_error('appointment_date', 'Date cannot be in the past')
            
            # Check if slot is already booked (Approved)
            elif Appointment.objects.filter(
                doctor=appointment.doctor,
                appointment_date=appointment.appointment_date,
                appointment_time=appointment.appointment_time,
                status='Approved'
            ).exists():
                form.add_error('appointment_time', 'This slot is already booked by another patient.')
            
            else:
                appointment.save()
                return redirect('appointment_status', appointment.id)
    else:
        form = AppointmentForm()

    return render(request, 'book_appointment.html', {
        'form': form,
        'appointments': appointments
    })


# ================= APPOINTMENT STATUS =========================

@login_required
def appointment_status(request, id):
    appointment = get_object_or_404(Appointment, id=id)
    return render(request, 'appointment_status.html', {
        'appointment': appointment
    })


# ================= MY APPOINTMENTS =========================

@login_required
def my_appointments(request):

    # 🚫 Prevent doctor from accessing patient page
    if DoctorRegister.objects.filter(user=request.user).exists():
        return HttpResponseForbidden("Doctors cannot access patient appointments.")

    patient = registration.objects.filter(user=request.user).first()

    if not patient:
        return HttpResponseForbidden("Patient profile not found.")

    status_filter = request.GET.get('status')
    sort = request.GET.get('sort', 'latest')

    appointments = Appointment.objects.filter(patient=patient)

    # FILTER BY STATUS
    if status_filter in ['Pending', 'Approved', 'Rejected']:
        appointments = appointments.filter(status=status_filter)

    # SORTING
    if sort == 'date_asc':
        appointments = appointments.order_by('appointment_date', 'appointment_time')
    elif sort == 'date_desc':
        appointments = appointments.order_by('-appointment_date', '-appointment_time')
    else:
        appointments = appointments.order_by('-created_at')

    return render(request, 'my_appointments.html', {
        'appointments': appointments,
        'status_filter': status_filter,
        'sort': sort
    })
#=================== CONTACT FORM =================
@login_required
def contact_suggestion(request):
    if request.method == "POST":
        form = ContactForm(request.POST)

        if form.is_valid():
            contact = form.save()

            # ===== EMAIL TO ADMIN =====
            send_mail(
                subject="New Suggestion Received",
                message=f"""
New Suggestion Submitted

Name: {contact.name}
Email: {contact.email}

Message:
{contact.message}
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.EMAIL_HOST_USER],
            )

            # ===== EMAIL TO USER =====
            send_mail(
                subject="Thank you for contacting ClinicOn CareSync",
                message=f"""
Hello {contact.name},

Thank you for sharing your suggestion with us.
Our team will review it and contact you if needed.

Your Message:
{contact.message}

Regards,
ClinicOn CareSync Team
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[contact.email],
            )

            messages.success(request, "Your message has been sent successfully!")
            return redirect("contact_suggestion")

    else:
        form = ContactForm()

    return render(request, "contact.html", {"form": form})

from django.db.models import Q

@login_required
def patient_suggestions(request):

    search = request.GET.get('search', '')
    sort = request.GET.get('sort', 'latest')

    suggestions = Checkup.objects.filter(
        patient__user=request.user
    ).select_related('doctor').order_by('-created_at')

    # 🔎 SEARCH BY DOCTOR NAME
    if search:
        suggestions = suggestions.filter(
            Q(doctor__doctor_name__icontains=search)
        )

    # 📅 SORTING
    if sort == 'oldest':
        suggestions = suggestions.order_by('created_at')
    else:
        suggestions = suggestions.order_by('-created_at')

    return render(request, 'view_suggestions.html', {
        'suggestions': suggestions,
        'search': search,
        'sort': sort
    })

# ================= SERVICES =================
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Service, DoctorRegister
from .forms import ServiceForm


@login_required
def available_services(request):
    services = Service.objects.all().order_by('-id')
    return render(request, 'services.html', {'services': services})


@login_required(login_url='doctor_login')
def add_service(request):
    doctor_id = request.session.get('doctor_id')
    if not doctor_id:
        return redirect('doctor_login')

    doctor = get_object_or_404(DoctorRegister, id=doctor_id)

    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES)
        if form.is_valid():
            service = form.save(commit=False)
            service.doctor = doctor
            service.save()
            messages.success(request, 'Service added successfully.')
            return redirect('manage_services')
    else:
        form = ServiceForm()

    return render(request, 'doctor/add_service.html', {
        'form': form,
        'doctor': doctor
    })


@login_required(login_url='doctor_login')
def manage_services(request):
    doctor_id = request.session.get('doctor_id')
    if not doctor_id:
        return redirect('doctor_login')

    doctor = get_object_or_404(DoctorRegister, id=doctor_id)
    services = Service.objects.filter(doctor=doctor).order_by('-id')

    return render(request, 'doctor/manage_services.html', {
        'services': services,
        'doctor': doctor
    })


@login_required(login_url='doctor_login')
def edit_service(request, id):
    doctor_id = request.session.get('doctor_id')
    if not doctor_id:
        return redirect('doctor_login')

    doctor = get_object_or_404(DoctorRegister, id=doctor_id)
    service = get_object_or_404(Service, id=id, doctor=doctor)

    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES, instance=service)
        if form.is_valid():
            updated_service = form.save(commit=False)
            updated_service.doctor = doctor
            updated_service.save()
            messages.success(request, 'Service updated successfully.')
            return redirect('manage_services')
    else:
        form = ServiceForm(instance=service)

    return render(request, 'doctor/edit_service.html', {
        'form': form,
        'doctor': doctor,
        'service': service
    })


@login_required(login_url='doctor_login')
def delete_service(request, id):
    doctor_id = request.session.get('doctor_id')
    if not doctor_id:
        return redirect('doctor_login')

    doctor = get_object_or_404(DoctorRegister, id=doctor_id)
    service = get_object_or_404(Service, id=id, doctor=doctor)

    service.delete()
    messages.success(request, 'Service deleted successfully.')
    return redirect('manage_services')

# ================= LOGOUT =================

def user_logout(request):
    # Check if user is a doctor before logging out
    is_doctor = False
    if request.user.is_authenticated:
        is_doctor = DoctorRegister.objects.filter(user=request.user).exists()
    
    logout(request)
    
    if is_doctor:
        return redirect('doctor_login')
    return redirect('login')


def index(request):
    services = Service.objects.all().order_by('-id')
    return render(request, 'index.html', {'services': services})

# ================= CATEGORY =================

def doctor_category(request):
    if request.method == "POST":
        department = Department.objects.get(id=request.POST['department_id'])
        DoctorCategory.objects.create(
            category_name=request.POST['category_name'],
            department=department
        )
        return redirect('doctor_category')

    return render(request, 'admin/doctor_category.html', {
        'categories': DoctorCategory.objects.all(),
        'departments': Department.objects.all()
    })


def edit_category(request, id):
    category = get_object_or_404(DoctorCategory, id=id)

    if request.method == "POST":
        category.category_name = request.POST['category_name']
        category.department_id = request.POST['department_id']
        category.save()
        return redirect('doctor_category')

    return render(request, 'admin/edit_category.html', {
        'category': category,
        'departments': Department.objects.all()
    })


def delete_category(request, id):
    DoctorCategory.objects.get(id=id).delete()
    return redirect('doctor_category')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
import re

from .models import (
    DoctorRegister,
    Department,
    DoctorCategory
)
# ================= IMPORTS =================
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator

from .models import DoctorRegister, Department, DoctorCategory


# =====================================================
# DOCTOR REGISTER (REQUEST → PENDING)
# =====================================================
def doctor_register(request):
    if request.method == "POST":
        doctor_name = request.POST.get('doctor_name')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        department_id = request.POST.get('department')
        category_id = request.POST.get('category')
        qualification = request.POST.get('qualification')
        experience = request.POST.get('experience')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        photo = request.FILES.get('photo')
        certificate = request.FILES.get('certificate')

        # ---------- VALIDATION ----------
        if not all([doctor_name, email, mobile, department_id, category_id]):
            messages.error(request, "All fields are required")
            return redirect('doctor_register')

        if User.objects.filter(username=email).exists():
            messages.error(request, "Email already registered")
            return redirect('doctor_register')

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect('doctor_register')

        if len(password) < 8 or not re.search(r"\d", password):
            messages.error(request, "Password must be at least 8 characters & contain a number")
            return redirect('doctor_register')

        if not photo or not certificate:
            messages.error(request, "Doctor photo and certificate required")
            return redirect('doctor_register')

        # ---------- CREATE USER ----------
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        # ---------- CREATE DOCTOR (PENDING) ----------
        DoctorRegister.objects.create(
            user=user,
            doctor_name=doctor_name,
            email=email,
            mobile=mobile,
            department_id=department_id,
            category_id=category_id,
            qualification=qualification,
            experience=experience,
            photo=photo,
            certificate=certificate,
            is_approved=False
        )

        messages.success(request, "Registration successful. Wait for admin approval.")
        return redirect('doctor_login')

    return render(request, 'doctor/doctor_register.html', {
        'departments': Department.objects.all(),
        'categories': DoctorCategory.objects.all()
    })


# =====================================================
# DOCTOR LOGIN (BLOCK UNTIL APPROVED)
# =====================================================
def doctor_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(username=email, password=password)

        if not user:
            return render(request, "doctor/doctor_login.html", {
                "error": "Invalid email or password"
            })

        try:
            doctor = DoctorRegister.objects.get(user=user)
        except DoctorRegister.DoesNotExist:
            return render(request, "doctor/doctor_login.html", {
                "error": "Doctor profile not found"
            })

        if not doctor.is_approved:
            return render(request, "doctor/doctor_login.html", {
                "error": "Your account is pending admin approval"
            })

        login(request, user)
        request.session['doctor_id'] = doctor.id
        return redirect('doctor_dashboard')

    return render(request, "doctor/doctor_login.html")

# =====================================================
# DOCTOR FORGOT PASSWORD
# =====================================================
def doctor_forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(username=email)
            DoctorRegister.objects.get(user=user)
        except:
            return render(request, "doctor/doctor_forgot_password.html", {
                "error": "Doctor account not found"
            })

        # Generate OTP
        otp = random.randint(100000, 999999)

        # Store in session
        request.session["doctor_reset_email"] = email
        request.session["doctor_reset_otp"] = str(otp)

        # Send Email
        subject = "Doctor Password Reset OTP"
        message = f"""
                    Hello Doctor,Your OTP for password reset is: {otp}Do not share this OTP with anyone.Hospital Management System
"""
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        return redirect("doctor_verify_otp")

    return render(request, "doctor/doctor_forgot_password.html")

# =====================================================
# DOCTOR VERIFY OTP
# =====================================================
def doctor_verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        session_otp = request.session.get("doctor_reset_otp")

        if entered_otp == session_otp:
            return redirect("doctor_reset_password")
        else:
            return render(request, "doctor/doctor_verify_otp.html", {
                "error": "Invalid OTP"
            })

    return render(request, "doctor/doctor_verify_otp.html")

# =====================================================
# DOCTOR RESET PASSWORD
# =====================================================
def doctor_reset_password(request):
    if request.method == "POST":
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            return render(request, "doctor/doctor_reset_password.html", {
                "error": "Passwords do not match"
            })

        email = request.session.get("doctor_reset_email")

        if not email:
            return redirect("doctor_forgot_password")

        user = User.objects.get(username=email)
        user.password = make_password(password)
        user.save()

        # Clear only OTP session
        request.session.pop("doctor_reset_email", None)
        request.session.pop("doctor_reset_otp", None)

        return redirect("doctor_login")

    return render(request, "doctor/doctor_reset_password.html")

# =====================================================
# DOCTOR DASHBOARD
# =====================================================
@login_required(login_url='doctor_login')
def doctor_dashboard(request):
    doctor_id = request.session.get('doctor_id')
    if not doctor_id:
        return redirect('doctor_login')

    doctor = DoctorRegister.objects.get(id=doctor_id)

    appointments = Appointment.objects.filter(doctor=doctor)

    total_appointments = appointments.count()
    approved_appointments = appointments.filter(status="Approved").count()
    pending_appointments = appointments.filter(status="Pending").count()
    rejected_appointments = appointments.filter(status="Rejected").count()

    total_services = Service.objects.filter(doctor=doctor).count()

    return render(request, 'doctor/doctor_dashboard.html', {
        'total_appointments': total_appointments,
        'approved_appointments': approved_appointments,
        'pending_appointments': pending_appointments,
        'rejected_appointments': rejected_appointments,
        'total_services': total_services,
    })

# =====================================================
# DOCTOR LOGOUT
# =====================================================
def doctor_logout(request):
    logout(request)
    return redirect('doctor_login')


# =====================================================
# ADMIN: DOCTOR LIST
# =====================================================
@login_required
def doctor_list(request):
    doctors = DoctorRegister.objects.all().order_by('-id')
    search = request.GET.get('search')

    if search:
        doctors = doctors.filter(doctor_name__icontains=search)

    paginator = Paginator(doctors, 5)
    doctors = paginator.get_page(request.GET.get('page'))

    return render(request, 'admin/doctor_list.html', {
        'doctors': doctors,
        'search': search
    })


# =====================================================
# ADMIN: APPROVE DOCTOR
# =====================================================
@login_required
def approve_doctor(request, id):
    doctor = get_object_or_404(DoctorRegister, id=id)
    doctor.is_approved = True
    doctor.save()

    messages.success(request, "Doctor approved successfully")
    return redirect('doctor_list')


# =====================================================
# ADMIN: REJECT DOCTOR
# =====================================================
@login_required
def reject_doctor(request, id):
    doctor = get_object_or_404(DoctorRegister, id=id)
    doctor.user.delete()  # deletes doctor + user
    messages.error(request, "Doctor rejected")
    return redirect('doctor_list')


# =====================================================
# ADMIN: EDIT DOCTOR
# =====================================================
@login_required
def edit_doctor(request, id):
    doctor = get_object_or_404(DoctorRegister, id=id)

    if request.method == "POST":
        doctor.doctor_name = request.POST.get('doctor_name')
        doctor.mobile = request.POST.get('mobile')
        doctor.qualification = request.POST.get('qualification')
        doctor.experience = request.POST.get('experience')
        doctor.department_id = request.POST.get('department_id')
        doctor.category_id = request.POST.get('category_id')

        if 'photo' in request.FILES:
            doctor.photo = request.FILES['photo']

        if 'certificate' in request.FILES:
            doctor.certificate = request.FILES['certificate']

        doctor.save()
        messages.success(request, "Doctor updated successfully")
        return redirect('doctor_list')

    return render(request, 'admin/edit_doctor.html', {
        'doctor': doctor,
        'departments': Department.objects.all(),
        'categories': DoctorCategory.objects.all()
    })


# =====================================================
# ADMIN: DELETE DOCTOR
# =====================================================
@login_required
def delete_doctor(request, id):
    doctor = get_object_or_404(DoctorRegister, id=id)
    doctor.user.delete()
    messages.success(request, "Doctor deleted successfully")
    return redirect('doctor_list')


@login_required(login_url='doctor_login')
def doctor_appointments(request):
    try:
        doctor = DoctorRegister.objects.get(user=request.user)
    except DoctorRegister.DoesNotExist:
        return redirect('doctor_login')

    appointments = Appointment.objects.filter(doctor=doctor).order_by('-appointment_date')

    return render(request, 'doctor/doctor_appointments.html', {
        'appointments': appointments,
        'doctor': doctor
    })


# ================= DOCTOR UPDATE APPOINTMENT STATUS =================

@login_required(login_url='doctor_login')
def update_appointment_status(request, id, action):

    # Check if logged-in user is doctor
    doctor = DoctorRegister.objects.filter(user=request.user).first()

    if not doctor:
        return HttpResponseForbidden("Only doctors can update appointment status.")

    appointment = get_object_or_404(Appointment, id=id, doctor=doctor)

    if action == "approve":
        # Check if slot is already booked (Approved)
        if Appointment.objects.filter(
            doctor=appointment.doctor,
            appointment_date=appointment.appointment_date,
            appointment_time=appointment.appointment_time,
            status='Approved'
        ).exclude(id=id).exists():
            messages.error(request, "This slot is already booked by another approved appointment.")
            return redirect('doctor_appointments')

        appointment.status = "Approved"

        # Auto-reject other pending appointments for same slot
        Appointment.objects.filter(
            doctor=appointment.doctor,
            appointment_date=appointment.appointment_date,
            appointment_time=appointment.appointment_time,
            status='Pending'
        ).exclude(id=id).update(status='Rejected')

        messages.success(request, "Appointment approved successfully. Patient can now pay the fee.")

    elif action == "reject":
        appointment.status = "Rejected"
        messages.error(request, "Appointment rejected.")

    appointment.save()

    return redirect('doctor_appointments')

# ================= DOCTOR ADD SUGGESTION =================

@login_required(login_url='doctor_login')
def add_suggestion(request, appointment_id):

    doctor = DoctorRegister.objects.filter(user=request.user).first()

    if not doctor:
        return HttpResponseForbidden("Only doctors can add suggestions.")

    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Ensure doctor owns this appointment
    if appointment.doctor != doctor:
        return HttpResponseForbidden("You are not authorized.")

    # Prevent duplicate suggestion
    if hasattr(appointment, 'checkup'):
        messages.warning(request, "Suggestion already added.")
        return redirect('doctor_appointments')

    if request.method == 'POST':
        form = CheckupForm(request.POST)

        if form.is_valid():
            checkup = form.save(commit=False)
            checkup.appointment = appointment
            checkup.doctor = doctor
            checkup.patient = appointment.patient
            checkup.save()

            messages.success(request, "Suggestion saved successfully.")
            return redirect('doctor_appointments')
    else:
        form = CheckupForm()

    return render(request, 'doctor/add_suggestion.html', {
        'form': form,
        'appointment': appointment
    })

# ================= DOCTOR PROFILE UPDATE =================
@login_required(login_url='doctor_login')
def doctor_profile(request):

    doctor_id = request.session.get('doctor_id')

    if not doctor_id:
        return redirect('doctor_login')

    doctor = get_object_or_404(DoctorRegister, id=doctor_id)

    if request.method == "POST":
        doctor.doctor_name = request.POST.get('doctor_name')
        doctor.mobile = request.POST.get('mobile')
        doctor.qualification = request.POST.get('qualification')
        doctor.experience = request.POST.get('experience')

        # optional image update
        if request.FILES.get('photo'):
            doctor.photo = request.FILES.get('photo')

        doctor.save()

        messages.success(request, "Profile updated successfully!")
        return redirect('doctor_profile')

    return render(request, 'doctor/profile.html', {
        'doctor': doctor
    })
    


@login_required(login_url='doctor_login')
def doctor_patient_feedback(request):

    # Check if logged-in user is doctor
    try:
        doctor = request.user.doctorregister
    except Exception:
        return HttpResponseForbidden("Only doctors can access feedback.")

    date_filter = request.GET.get('date')

    feedbacks = Contact.objects.filter(doctor=doctor).order_by('-created_at')

    if date_filter:
        feedbacks = feedbacks.filter(created_at__date=date_filter)

    return render(request, "doctor/patient_feedback.html", {
        "feedbacks": feedbacks,
        "selected_date": date_filter
    })

# ================= RAZORPAY PAYMENT =========================

@login_required
def initiate_payment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Security check: only patient can pay for their own appointment
    patient = registration.objects.filter(user=request.user).first()
    if appointment.patient != patient:
        return HttpResponseForbidden("You are not authorized to pay for this appointment.")

    if appointment.status != 'Approved':
        messages.error(request, "You can only pay for approved appointments.")
        return redirect('my_appointments')

    if appointment.is_paid:
        messages.info(request, "This appointment is already paid.")
        return redirect('my_appointments')

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    # Amount in paise (500 INR = 50000 paise)
    amount = settings.APPOINTMENT_FEE * 100
    currency = "INR"

    # Create Razorpay Order
    data = {
        "amount": amount,
        "currency": currency,
        "receipt": f"receipt_{appointment.id}",
        "payment_capture": 1 # 1 means capture payment automatically
    }
    
    try:
        order = client.order.create(data=data)
        appointment.razorpay_order_id = order['id']
        appointment.save()

        context = {
            'appointment': appointment,
            'order_id': order['id'],
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'amount': amount,
            'currency': currency,
            'patient_name': patient.username,
            'patient_email': patient.email,
            'patient_mobile': patient.mobile,
        }
        return render(request, 'payment.html', context)
    except Exception as e:
        messages.error(request, f"Something went wrong with Razorpay: {str(e)}")
        return redirect('my_appointments')

@csrf_exempt
def payment_callback(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id')
        order_id = request.POST.get('razorpay_order_id')
        signature = request.POST.get('razorpay_signature')

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        try:
            # Verify the payment signature
            client.utility.verify_payment_signature(params_dict)
            
            # Update appointment status
            appointment = Appointment.objects.get(razorpay_order_id=order_id)
            appointment.is_paid = True
            appointment.razorpay_payment_id = payment_id
            appointment.razorpay_signature = signature
            appointment.save()

            # Send Invoice Email after successful payment
            send_appointment_invoice_email(appointment)

            messages.success(request, "Payment successful! Your booking is confirmed and invoice sent.")
            return redirect('my_appointments')
        except Exception as e:
            messages.error(request, "Payment verification failed.")
            return redirect('my_appointments')

    return redirect('my_appointments')
