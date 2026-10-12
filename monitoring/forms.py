from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import TrafficVideo, Violation


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleVideoField(forms.FileField):
    def clean(self, data, initial=None):
        files = data if isinstance(data, (list, tuple)) else [data]
        return [super(MultipleVideoField, self).clean(item, initial) for item in files]

class RegistrationForm(UserCreationForm):
    email = forms.EmailField()
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

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

class ViolationForm(forms.ModelForm):
    class Meta:
        model = Violation
        fields = ("source_name", "vehicle_number", "offence_type", "fine_amount", "location", "confidence", "evidence")
