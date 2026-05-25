from django import forms
from .models import *

class AppointmentForm(forms.ModelForm):

    appointment_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )

    appointment_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control'
        })
    )

    class Meta:
        model = Appointment
        fields = ['doctor', 'appointment_date', 'appointment_time']

        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-control'}),
        }

#----------
class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['doctor', 'name', 'email', 'message']
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    
#-----------------DOCTOR CHECKUP SUGGESTION FORM -----------------

class CheckupForm(forms.ModelForm):
    class Meta:
        model = Checkup
        fields = ['suggestion']
        widgets = {
            'suggestion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter patient suggestion here...'
            })
        }

    def clean_suggestion(self):
        suggestion = self.cleaned_data.get('suggestion')
        if len(suggestion.strip()) < 10:
            raise forms.ValidationError("Suggestion must be at least 10 characters.")
        return suggestion

#-----------------DOCTOR AVAILABILITY FORM -----------------
class DoctorAvailabilityForm(forms.ModelForm):

    class Meta:
        model = DoctorAvailability
        fields = ['doctor', 'available_date', 'start_time', 'end_time']

        widgets = {
            'available_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'doctor': forms.Select(attrs={'class': 'form-select'}),
        }

#-----------------SERVICE FORM -----------------
class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['service_name', 'short_description', 'service_image', 'icon_class']
        widgets = {
            'service_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter service name'
            }),
            'short_description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter short description',
                'rows': 4
            }),
            'service_image': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'icon_class': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: fa-solid fa-heart-pulse'
            }),
        }