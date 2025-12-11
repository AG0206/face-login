from django.db import models
from django.contrib.auth.models import User

class FaceRecord(models.Model):
    """
    Model to store facial recognition data
    """
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='face_images/')
    encoding = models.TextField(blank=True, null=True)  # For storing face encodings
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class RecognitionLog(models.Model):
    """
    Model to log facial recognition attempts
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to='recognition_logs/')
    result = models.TextField()  # JSON field to store recognition results
    confidence = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Recognition log {self.id} - {self.timestamp}"

# Smart Library Models
class Franchise(models.Model):
    """
    Model to represent a franchise/branch of the library
    """
    name = models.CharField(max_length=200, unique=True)
    location = models.CharField(max_length=300)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.location}"

class UserProfile(models.Model):
    """
    Extended profile for all users in the system
    """
    USER_TYPE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('franchise_owner', 'Franchise Owner'),
        ('student', 'Student/User'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    franchise = models.ForeignKey(Franchise, on_delete=models.SET_NULL, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    face_record = models.ForeignKey(FaceRecord, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.user_type}"

class Book(models.Model):
    """
    Model to represent books in the library
    """
    title = models.CharField(max_length=300)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=20, unique=True)
    publisher = models.CharField(max_length=200)
    publication_date = models.DateField()
    genre = models.CharField(max_length=100)
    franchise = models.ForeignKey(Franchise, on_delete=models.CASCADE)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} by {self.author}"

class BookIssue(models.Model):
    """
    Model to track book issues and returns
    """
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    issue_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    return_date = models.DateTimeField(null=True, blank=True)
    is_returned = models.BooleanField(default=False)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def __str__(self):
        status = "Returned" if self.is_returned else "Issued"
        return f"{self.book.title} - {self.user.username} ({status})"