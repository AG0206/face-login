from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Franchise, UserProfile, Book

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    franchise = forms.ModelChoiceField(queryset=Franchise.objects.filter(is_active=True))
    phone_number = forms.CharField(max_length=20, required=False)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 
                  'franchise', 'phone_number')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            
            # Create or update user profile with fixed user_type='student'
            user_profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'user_type': 'student',
                    'franchise': self.cleaned_data['franchise'],
                    'phone_number': self.cleaned_data['phone_number']
                }
            )
            # If profile already existed, update it
            if not created:
                user_profile.user_type = 'student'
                user_profile.franchise = self.cleaned_data['franchise']
                user_profile.phone_number = self.cleaned_data['phone_number']
                user_profile.save()
        return user

class FranchiseOwnerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    franchise_name = forms.CharField(max_length=200)
    franchise_location = forms.CharField(max_length=300)
    franchise_email = forms.EmailField()
    franchise_phone = forms.CharField(max_length=20)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            
            # Create franchise
            franchise = Franchise.objects.create(
                name=self.cleaned_data['franchise_name'],
                location=self.cleaned_data['franchise_location'],
                contact_email=self.cleaned_data['franchise_email'],
                contact_phone=self.cleaned_data['franchise_phone']
            )
            
            # Create or update user profile
            user_profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'user_type': 'franchise_owner',
                    'franchise': franchise
                }
            )
            # If profile already existed, update it
            if not created:
                user_profile.user_type = 'franchise_owner'
                user_profile.franchise = franchise
                user_profile.save()
        return user

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ('title', 'author', 'isbn', 'publisher', 'publication_date', 'genre', 
                  'total_copies', 'available_copies')
        widgets = {
            'publication_date': forms.DateInput(attrs={'type': 'date'}),
        }

class BookIssueForm(forms.Form):
    book = forms.ModelChoiceField(queryset=Book.objects.none())
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # Filter books by user's franchise and only available books
            try:
                user_profile = UserProfile.objects.get(user=user)
                self.fields['book'].queryset = Book.objects.filter(
                    franchise=user_profile.franchise,
                    available_copies__gt=0
                )
            except UserProfile.DoesNotExist:
                self.fields['book'].queryset = Book.objects.none()

class FranchiseEditForm(forms.ModelForm):
    class Meta:
        model = Franchise
        fields = ('name', 'location', 'contact_email', 'contact_phone', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
