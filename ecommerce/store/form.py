from django import forms
from .models import Customer
from django.contrib.auth import authenticate

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(label='Email', max_length=254, required=True)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')

        if not Customer.objects.filter(email=email).exists():
            raise forms.ValidationError("No User Registered with this email.")
        
class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(label='New Password', min_length=8)
    confirm_password = forms.CharField(label='Confirm Password', min_length=8)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")