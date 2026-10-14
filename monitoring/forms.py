from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import TrafficVideo, VehicleProfile, normalize_vehicle_number


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleVideoField(forms.FileField):
    def clean(self, data, initial=None):
        files = data if isinstance(data, (list, tuple)) else [data]
        return [super(MultipleVideoField, self).clean(item, initial) for item in files]

class RegistrationForm(UserCreationForm):
    email = forms.EmailField()
    vehicle_number = forms.CharField(max_length=32, label="Vehicle number plate")

    def clean_vehicle_number(self):
        vehicle_number = normalize_vehicle_number(self.cleaned_data["vehicle_number"])
        if VehicleProfile.objects.filter(vehicle_number=vehicle_number).exists():
            raise forms.ValidationError("This vehicle number is already registered")
        return vehicle_number

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class PasswordResetLookupForm(forms.Form):
    email = forms.EmailField()
    vehicle_number = forms.CharField(max_length=32, label="Vehicle plate number")

    def clean_vehicle_number(self):
        return normalize_vehicle_number(self.cleaned_data["vehicle_number"])


class PasswordResetConfirmForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput, min_length=8, label="New password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, min_length=8, label="Confirm new password")

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("new_password") and cleaned_data.get("new_password") != cleaned_data.get("confirm_password"):
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned_data

class VideoForm(forms.ModelForm):
    source = MultipleVideoField(widget=MultipleFileInput(attrs={"accept": "video/*"}))

    class Meta:
        model = TrafficVideo
        fields = ("source",)
    def clean_source(self):
        videos = self.cleaned_data["source"]
        for video in videos:
            if not video.name.lower().endswith((".mp4", ".mov", ".avi", ".mkv", ".mpeg", ".mpg", ".m4v")):
                raise forms.ValidationError("Upload a supported video format.")
            if video.size > 1024 * 1024 * 1024:
                raise forms.ValidationError("The maximum file size is 1 GB.")
        return videos

class FineReportForm(forms.Form):
    FINE_CHOICES = (("100", "₹100"), ("500", "₹500"), ("1000", "₹1,000"))
    vehicle_number = forms.CharField(max_length=32, label="Vehicle number plate")
    area = forms.ChoiceField()
    fine_amount = forms.TypedChoiceField(choices=FINE_CHOICES, coerce=int, label="Fine amount (INR)")
    evidence = forms.ImageField(label="Snapshot image", widget=forms.ClearableFileInput(attrs={"accept": ".jpg,.jpeg,.png,image/jpeg,image/png"}))

    def __init__(self, *args, videos=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["area"].choices = [(video.area_name, video.area_name) for video in (videos or [])]

    def clean_vehicle_number(self):
        vehicle_number = normalize_vehicle_number(self.cleaned_data["vehicle_number"])
        if not VehicleProfile.objects.filter(vehicle_number=vehicle_number).exists():
            raise forms.ValidationError("No registered user has this vehicle number.")
        return vehicle_number

    def clean_evidence(self):
        evidence = self.cleaned_data["evidence"]
        if not evidence.name.lower().endswith((".jpg", ".jpeg", ".png")):
            raise forms.ValidationError("Upload a JPG, JPEG, or PNG image.")
        return evidence
