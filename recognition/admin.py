from django.contrib import admin
from .models import FaceRecord, RecognitionLog, Franchise, UserProfile, Book, BookIssue

@admin.register(Franchise)
class FranchiseAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'contact_email', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'location', 'contact_email')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'franchise', 'phone_number', 'created_at')
    list_filter = ('user_type', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone_number')

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'franchise', 'available_copies', 'total_copies', 'created_at')
    list_filter = ('franchise', 'genre', 'created_at')
    search_fields = ('title', 'author', 'isbn')

@admin.register(BookIssue)
class BookIssueAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'issue_date', 'due_date', 'return_date', 'is_returned')
    list_filter = ('is_returned', 'issue_date', 'due_date')
    search_fields = ('book__title', 'user__username')
    date_hierarchy = 'issue_date'

# Register the existing models
admin.site.register(FaceRecord)
admin.site.register(RecognitionLog)