from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
import cv2
import numpy as np
import os
import json
import logging
import base64
import tempfile
from django.core.files.uploadedfile import TemporaryUploadedFile
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import models directly
from .models import FaceRecord, RecognitionLog, Franchise, UserProfile, Book, BookIssue
from .forms import UserRegistrationForm, FranchiseOwnerRegistrationForm, BookForm, BookIssueForm, FranchiseEditForm
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm, AuthenticationForm

# Create your views here.
def index(request):
    """
    Main landing page for the Smart Library system
    """
    return render(request, 'recognition/index.html')

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect based on user type
                try:
                    if user.userprofile.user_type == 'super_admin':
                        return redirect('recognition:super_admin_dashboard')
                    elif user.userprofile.user_type == 'franchise_owner':
                        return redirect('recognition:franchise_owner_dashboard')
                    else:
                        return redirect('recognition:user_dashboard')
                except UserProfile.DoesNotExist:
                    # Handle case where user profile doesn't exist
                    messages.error(request, 'User profile not found. Please contact administrator.')
                    return redirect('recognition:login')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        # If user is already authenticated, redirect to appropriate dashboard
        if request.user.is_authenticated:
            try:
                if request.user.userprofile.user_type == 'super_admin':
                    return redirect('recognition:super_admin_dashboard')
                elif request.user.userprofile.user_type == 'franchise_owner':
                    return redirect('recognition:franchise_owner_dashboard')
                else:
                    return redirect('recognition:user_dashboard')
            except UserProfile.DoesNotExist:
                # If user profile doesn't exist, logout and show login page
                logout(request)
                messages.error(request, 'User profile not found. Please contact administrator.')
        
        # Initialize form for GET requests
        form = AuthenticationForm()
    
    # Use the simplified template for login
    return render(request, 'recognition/login_simple.html', {'form': form})

@require_POST
def user_logout(request):
    """
    Handle user logout
    """
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('recognition:index')

def user_register(request):
    """
    Handle user registration (students only)
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('recognition:login')
        else:
            # Print form errors for debugging
            print("Form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'recognition/register.html', {'form': form})

def franchise_owner_register(request):
    """
    Handle franchise owner registration
    """
    if request.method == 'POST':
        form = FranchiseOwnerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Franchise registration successful. Please log in.')
            return redirect('recognition:login')
    else:
        form = FranchiseOwnerRegistrationForm()
    
    return render(request, 'recognition/franchise_owner_register.html', {'form': form})

@login_required
def super_admin_dashboard(request):
    """
    Dashboard for Super Admin (HQ)
    """
    # Check if user is super admin
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.user_type != 'super_admin':
            messages.error(request, 'Access denied.')
            return redirect('recognition:index')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('recognition:index')
    
    # Get statistics
    total_franchises = Franchise.objects.count()
    total_users = UserProfile.objects.count()
    total_books = Book.objects.count()
    total_issued_books = BookIssue.objects.filter(is_returned=False).count()
    
    # Get recent franchises
    recent_franchises = Franchise.objects.order_by('-created_at')[:5]
    
    # Get franchise statistics
    franchise_stats = Franchise.objects.annotate(
        book_count=Count('book'),
        user_count=Count('userprofile')
    ).order_by('-book_count')[:5]
    
    # Get all users for password reset functionality
    users = User.objects.all().order_by('username')
    
    context = {
        'total_franchises': total_franchises,
        'total_users': total_users,
        'total_books': total_books,
        'total_issued_books': total_issued_books,
        'recent_franchises': recent_franchises,
        'franchise_stats': franchise_stats,
        'users': users,
    }
    
    return render(request, 'recognition/super_admin_dashboard.html', context)

@login_required
def reset_user_password(request, user_id):
    """
    Allow super admin to reset password for any user
    """
    # Check if user is super admin
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.user_type != 'super_admin':
            messages.error(request, 'Access denied.')
            return redirect('recognition:index')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('recognition:index')
    
    # Get the user whose password needs to be reset
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('recognition:super_admin_dashboard')
    
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Password for {user.username} has been reset successfully.')
            return redirect('recognition:super_admin_dashboard')
    else:
        form = SetPasswordForm(user)
    
    return render(request, 'recognition/reset_user_password.html', {
        'form': form,
        'target_user': user
    })

@login_required
def franchise_owner_dashboard(request):
    """
    Dashboard for Franchise Owner
    """
    # Check if user is franchise owner
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.user_type != 'franchise_owner':
            messages.error(request, 'Access denied.')
            return redirect('recognition:index')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('recognition:index')
    
    # Get franchise
    franchise = profile.franchise
    
    # Get statistics for this franchise
    total_books = Book.objects.filter(franchise=franchise).count()
    total_users = UserProfile.objects.filter(franchise=franchise).count()
    issued_books = BookIssue.objects.filter(book__franchise=franchise, is_returned=False).count()
    
    # Calculate total revenue from fines
    from django.db.models import Sum
    total_revenue = BookIssue.objects.filter(
        book__franchise=franchise, 
        is_returned=True
    ).aggregate(
        total_fines=Sum('fine_amount')
    )['total_fines'] or 0.00
    
    # Get recent books
    recent_books = Book.objects.filter(franchise=franchise).order_by('-created_at')[:5]
    
    context = {
        'franchise': franchise,
        'total_books': total_books,
        'total_users': total_users,
        'issued_books': issued_books,
        'total_revenue': total_revenue,
        'recent_books': recent_books,
    }
    
    return render(request, 'recognition/franchise_owner_dashboard.html', context)


@login_required
def franchise_edit(request):
    """
    Handle franchise details editing for franchise owners
    """
    # Check if user is franchise owner
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.user_type != 'franchise_owner':
            messages.error(request, 'Access denied.')
            return redirect('recognition:index')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('recognition:index')
    
    # Get franchise
    franchise = profile.franchise
    
    if request.method == 'POST':
        form = FranchiseEditForm(request.POST, instance=franchise)
        if form.is_valid():
            form.save()
            messages.success(request, 'Franchise details updated successfully.')
            return redirect('recognition:franchise_owner_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FranchiseEditForm(instance=franchise)
    
    return render(request, 'recognition/franchise_edit.html', {'form': form, 'franchise': franchise})


@login_required
def franchise_manage_users(request):
    """
    Handle user management for franchise owners
    """
    # Check if user is franchise owner
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.user_type != 'franchise_owner':
            messages.error(request, 'Access denied.')
            return redirect('recognition:index')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('recognition:index')
    
    # Get franchise
    franchise = profile.franchise
    
    # Get all users for this franchise with annotated book issue counts
    from django.db.models import Count, Q
    users = UserProfile.objects.filter(franchise=franchise).select_related('user').annotate(
        issued_books_count=Count('user__bookissue', filter=Q(user__bookissue__is_returned=False))
    )
    
    # Pagination
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'franchise': franchise,
        'page_obj': page_obj,
    }
    
    return render(request, 'recognition/franchise_manage_users.html', context)


@login_required
def user_book_history(request, user_id):
    """
    Display book issue/return history for a specific user
    """
    # Check if user is franchise owner
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.user_type != 'franchise_owner':
            messages.error(request, 'Access denied.')
            return redirect('recognition:index')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('recognition:index')
    
    # Get the user profile for the requested user
    try:
        user_profile = UserProfile.objects.select_related('user').get(id=user_id, franchise=profile.franchise)
    except UserProfile.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('recognition:franchise_manage_users')
    
    # Get book issue history for this user
    book_issues = BookIssue.objects.filter(user=user_profile.user).select_related('book').order_by('-issue_date')
    
    # Pagination
    paginator = Paginator(book_issues, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'user_profile': user_profile,
        'page_obj': page_obj,
    }
    
    return render(request, 'recognition/user_book_history.html', context)


@login_required
def franchise_transactions(request):
    """
    Display all book transactions for the franchise
    """
    # Check if user is franchise owner
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.user_type != 'franchise_owner':
            messages.error(request, 'Access denied.')
            return redirect('recognition:index')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('recognition:index')
    
    # Get franchise
    franchise = profile.franchise
    
    # Get all book transactions for this franchise
    transactions = BookIssue.objects.filter(book__franchise=franchise).select_related('book', 'user').order_by('-issue_date')
    
    # Pagination
    paginator = Paginator(transactions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'franchise': franchise,
        'page_obj': page_obj,
    }
    
    return render(request, 'recognition/franchise_transactions.html', context)

@login_required
def user_dashboard(request):
    """
    Dashboard for regular users/students
    """
    # Check if user is student
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.user_type != 'student':
            messages.error(request, 'Access denied.')
            return redirect('recognition:index')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('recognition:index')
    
    # Get user's issued books
    issued_books = BookIssue.objects.filter(user=request.user, is_returned=False)
    returned_books = BookIssue.objects.filter(user=request.user, is_returned=True).order_by('-return_date')[:5]
    
    # Get user's outstanding fines (unpaid fines for returned books)
    outstanding_fines = BookIssue.objects.filter(
        user=request.user, 
        is_returned=True,
        fine_amount__gt=0
    )
    
    # Calculate total outstanding fine amount
    from django.db.models import Sum
    total_outstanding_fines = outstanding_fines.aggregate(
        total=Sum('fine_amount')
    )['total'] or 0.00
    
    # Get user's franchise
    franchise = profile.franchise
    
    context = {
        'issued_books': issued_books,
        'returned_books': returned_books,
        'outstanding_fines': outstanding_fines,
        'total_outstanding_fines': total_outstanding_fines,
        'franchise': franchise,
    }
    
    return render(request, 'recognition/user_dashboard.html', context)

@login_required
def book_list(request):
    """
    List books with search functionality
    """
    # Get user profile to filter by franchise
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('recognition:index')
    
    # Filter books based on user type
    if profile.user_type == 'super_admin':
        books = Book.objects.all()
    else:
        books = Book.objects.filter(franchise=profile.franchise)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) | 
            Q(author__icontains=search_query) | 
            Q(isbn__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(books, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    
    return render(request, 'recognition/book_list.html', context)

@login_required
def book_create(request):
    """
    Handle book creation for franchise owners
    """
    # Check if user is franchise owner
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.user_type != 'franchise_owner':
            messages.error(request, 'Access denied.')
            return redirect('recognition:index')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('recognition:index')
    
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save(commit=False)
            book.franchise = profile.franchise
            book.save()
            messages.success(request, f'Book "{book.title}" added successfully.')
            return redirect('recognition:franchise_owner_dashboard')
    else:
        form = BookForm()
    
    return render(request, 'recognition/book_form.html', {'form': form, 'action': 'Add'})

@login_required
def book_edit(request, book_id):
    """
    Handle book editing for franchise owners
    """
    # Check if user is franchise owner
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.user_type != 'franchise_owner':
            messages.error(request, 'Access denied.')
            return redirect('recognition:index')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('recognition:index')
    
    try:
        book = Book.objects.get(id=book_id, franchise=profile.franchise)
    except Book.DoesNotExist:
        messages.error(request, 'Book not found.')
        return redirect('recognition:franchise_owner_dashboard')
    
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, f'Book "{book.title}" updated successfully.')
            return redirect('recognition:franchise_owner_dashboard')
    else:
        form = BookForm(instance=book)
    
    return render(request, 'recognition/book_form.html', {'form': form, 'action': 'Edit', 'book': book})

@login_required
def book_delete(request, book_id):
    """
    Handle book deletion for franchise owners
    """
    # Check if user is franchise owner
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.user_type != 'franchise_owner':
            messages.error(request, 'Access denied.')
            return redirect('recognition:index')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('recognition:index')
    
    try:
        book = Book.objects.get(id=book_id, franchise=profile.franchise)
    except Book.DoesNotExist:
        messages.error(request, 'Book not found.')
        return redirect('recognition:franchise_owner_dashboard')
    
    if request.method == 'POST':
        book_title = book.title
        book.delete()
        messages.success(request, f'Book "{book_title}" deleted successfully.')
        return redirect('recognition:franchise_owner_dashboard')
    
    return render(request, 'recognition/book_confirm_delete.html', {'book': book})

@login_required
def book_issue(request):
    """
    Handle book issue functionality for users
    """
    # Check if user is student
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.user_type != 'student':
            messages.error(request, 'Access denied.')
            return redirect('recognition:index')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('recognition:index')
    
    if request.method == 'POST':
        form = BookIssueForm(request.POST, user=request.user)
        if form.is_valid():
            book = form.cleaned_data['book']
            
            # Check if book is available
            if book.available_copies > 0:
                # Create book issue record
                BookIssue.objects.create(
                    book=book,
                    user=request.user,
                    due_date=timezone.now() + timezone.timedelta(days=14)  # 2 weeks
                )
                
                # Update available copies
                book.available_copies -= 1
                book.save()
                
                messages.success(request, f'Book "{book.title}" issued successfully.')
                return redirect('recognition:user_dashboard')
            else:
                messages.error(request, 'This book is not available.')
    else:
        form = BookIssueForm(user=request.user)
    
    return render(request, 'recognition/book_issue.html', {'form': form})

@login_required
def book_return(request, issue_id):
    """
    Handle book return functionality
    """
    # Check if user is student
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('recognition:index')
    
    try:
        book_issue = BookIssue.objects.get(id=issue_id)
        
        # Check permissions
        if profile.user_type == 'student' and book_issue.user != request.user:
            messages.error(request, 'Access denied.')
            return redirect('recognition:index')
        elif profile.user_type == 'franchise_owner' and book_issue.book.franchise != profile.franchise:
            messages.error(request, 'Access denied.')
            return redirect('recognition:index')
    except BookIssue.DoesNotExist:
        messages.error(request, 'Book issue record not found.')
        return redirect('recognition:index')
    
    if request.method == 'POST':
        # Calculate fine if book is returned late
        from datetime import datetime
        from django.utils import timezone
        
        # Get current time
        now = timezone.now()
        
        # Check if book is returned late
        if now > book_issue.due_date:
            # Calculate days late
            days_late = (now - book_issue.due_date).days
            
            # Calculate fine (assuming $1 per day late)
            fine_rate_per_day = 1.00
            fine_amount = days_late * fine_rate_per_day
            
            # Set the fine amount (capped at a reasonable maximum)
            book_issue.fine_amount = min(fine_amount, 50.00)  # Maximum fine of $50
        else:
            # No fine if returned on time or early
            book_issue.fine_amount = 0.00
        
        # Mark book as returned
        book_issue.is_returned = True
        book_issue.return_date = now
        book_issue.save()
        
        # Update book availability
        book_issue.book.available_copies += 1
        book_issue.book.save()
        
        # Show appropriate message based on fine
        if book_issue.fine_amount > 0:
            messages.warning(request, f'Book "{book_issue.book.title}" returned {days_late} days late. A fine of ${book_issue.fine_amount:.2f} has been applied.')
        else:
            messages.success(request, f'Book "{book_issue.book.title}" returned successfully.')
        
        # Redirect based on user type
        if profile.user_type == 'student':
            return redirect('recognition:user_dashboard')
        else:
            return redirect('recognition:franchise_owner_dashboard')
    
    return render(request, 'recognition/book_return_confirm.html', {'book_issue': book_issue})

def detect_faces_page(request):
    """
    Page for face detection functionality
    """
    return render(request, 'recognition/detect.html')

def face_records_list(request):
    """
    List all face records
    """
    face_records = FaceRecord.objects.all().order_by('-created_at')
    paginator = Paginator(face_records, 10)  # Show 10 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'recognition/face_records_list.html', {'page_obj': page_obj})

def detect_faces(request):
    """
    Simple face detection endpoint
    """
    # This is a placeholder for actual face detection logic
    # In a real application, you would process an image here
    
    response_data = {
        'status': 'success',
        'message': 'Face detection endpoint ready',
        'library_status': {
            'opencv': 'available',
            'dlib': 'not installed (requires Visual Studio Build Tools)',
            'face_recognition': 'not installed (requires dlib)'
        }
    }
    
    return JsonResponse(response_data)

@csrf_exempt
def upload_and_detect(request):
    """
    Handle image upload and face detection
    """
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            # Get the uploaded image
            image_file = request.FILES['image']
            
            # In a real implementation, you would:
            # 1. Save the image temporarily
            # 2. Load it with OpenCV
            # 3. Apply face detection
            # 4. Return results
            
            result = {
                'status': 'success',
                'message': 'Image uploaded successfully',
                'note': 'Actual face detection requires dlib and face-recognition libraries',
                'filename': image_file.name,
                'size': image_file.size
            }
            
            return render(request, 'recognition/detect.html', {'result': json.dumps(result, indent=2)})
            
        except Exception as e:
            return render(request, 'recognition/detect.html', {'error': str(e)})
    
    return render(request, 'recognition/detect.html')

@login_required
def update_user_face(request):
    """
    Handle face recognition update for users
    """
    logger.debug(f"update_user_face called by user: {request.user.username}")
    
    # Check if user is student
    try:
        profile = UserProfile.objects.get(user=request.user)
        logger.debug(f"User profile found: {profile.user_type}")
        
        if profile.user_type != 'student':
            messages.error(request, 'Access denied.')
            return redirect('recognition:index')
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        messages.error(request, 'User profile not found.')
        return redirect('recognition:index')
    
    if request.method == 'POST':
        logger.debug("Processing POST request for face update")
        try:
            # Check if we have a captured image from camera
            captured_image_data = request.POST.get('captured_image')
            uploaded_file = request.FILES.get('image')
            
            logger.debug(f"Captured image data: {captured_image_data is not None}")
            logger.debug(f"Uploaded file: {uploaded_file is not None}")
            
            # Validate that we have either a captured image or uploaded file
            if not captured_image_data and not uploaded_file:
                messages.error(request, 'Please either upload an image or capture one using the camera.')
                return render(request, 'recognition/update_user_face.html')
            
            image_file = None
            
            if captured_image_data and captured_image_data.startswith('data:image'):
                logger.debug("Processing captured image from camera")
                # Process captured image from camera
                try:
                    format, imgstr = captured_image_data.split(';base64,') 
                    ext = format.split('/')[-1] 
                    logger.debug(f"Image format: {format}, extension: {ext}")
                    
                    # Decode the image data
                    import base64
                    img_data = base64.b64decode(imgstr)
                    logger.debug(f"Image data size: {len(img_data)} bytes")
                    
                    # Create a Django ContentFile directly from the decoded data
                    from django.core.files.base import ContentFile
                    image_file = ContentFile(img_data, name=f"captured_face.{ext}")
                    logger.debug(f"Created ContentFile: {image_file.name}")
                except Exception as e:
                    logger.error(f"Error processing captured image: {e}")
                    messages.error(request, f'Error processing captured image: {str(e)}')
                    return render(request, 'recognition/update_user_face.html')
                    
            elif uploaded_file:
                logger.debug(f"Using uploaded file: {uploaded_file.name}")
                # Use uploaded file
                image_file = uploaded_file
                logger.debug(f"Using uploaded file: {image_file.name}")
            
            if image_file:
                logger.debug("Processing image file for face detection")
                # Try to detect faces using OpenCV
                face_detected = detect_face_opencv(image_file)
                logger.debug(f"Face detection result: {face_detected}")
                
                if face_detected:
                    logger.debug("Face detected, creating/updating FaceRecord")
                    # Create or update FaceRecord for the user
                    face_record, created = FaceRecord.objects.get_or_create(
                        name=f"{request.user.first_name} {request.user.last_name}",
                    )
                    logger.debug(f"FaceRecord {'created' if created else 'retrieved'}: {face_record.id}")
                    
                    # Save the image
                    face_record.image = image_file
                    face_record.save()
                    logger.debug(f"FaceRecord image saved: {face_record.image}")
                    
                    # Update user profile with face record
                    profile.face_record = face_record
                    profile.save()
                    logger.debug(f"UserProfile updated with face_record: {profile.face_record.id}")
                    
                    messages.success(request, 'Face recognition data updated successfully.')
                    return redirect('recognition:user_dashboard')
                else:
                    messages.error(request, 'No face detected in the image. Please ensure your face is clearly visible, well-lit, and try again.')
            else:
                messages.error(request, 'Error processing image. Please try again.')
                
        except Exception as e:
            logger.error(f"Error in update_user_face: {e}", exc_info=True)
            messages.error(request, f'Error processing image: {str(e)}')
    
    return render(request, 'recognition/update_user_face.html')

def detect_face_opencv(image_file):
    """
    Detect faces in an image using OpenCV with multiple approaches
    """
    try:
        # Handle different types of image files
        if hasattr(image_file, 'read'):
            # For uploaded files, read the content
            image_data = image_file.read()
        elif isinstance(image_file, (bytes, bytearray)):
            # For raw bytes data
            image_data = image_file
        else:
            print(f"Error: Unsupported image file type: {type(image_file)}")
            return False
            
        # Convert to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        
        # Check if we have data
        if nparr.size == 0:
            print("Error: Empty image data")
            return False
            
        # Decode image
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            print("Error: Could not decode image")
            print(f"Image data size: {len(image_data) if image_data else 0}")
            print(f"NumPy array size: {nparr.size}")
            return False
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Load Haar cascade for face detection
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Try multiple detection approaches
        # Approach 1: Standard detection
        faces1 = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=3,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Approach 2: More lenient detection
        faces2 = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=2,
            minSize=(20, 20),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Approach 3: Try with histogram equalization for better contrast
        equalized = cv2.equalizeHist(gray)
        faces3 = face_cascade.detectMultiScale(
            equalized,
            scaleFactor=1.1,
            minNeighbors=3,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Use the approach that found the most faces
        all_faces = [faces1, faces2, faces3]
        best_faces = max(all_faces, key=len)
        
        # Print debug information
        print(f"Detected {len(best_faces)} faces in image using best approach")
        if len(best_faces) > 0:
            for i, (x, y, w, h) in enumerate(best_faces):
                print(f"Face {i}: x={x}, y={y}, w={w}, h={h}")
        
        # Return True if at least one face is detected
        return len(best_faces) > 0
    except Exception as e:
        print(f"Error in face detection: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_faces_opencv(uploaded_image, stored_image_path):
    """
    Compare two faces using OpenCV's face recognition (improved version)
    """
    try:
        # Read uploaded image - handle both file objects and raw bytes
        if hasattr(uploaded_image, 'read'):
            # For uploaded files, read the content
            uploaded_data = uploaded_image.read()
        elif isinstance(uploaded_image, (bytes, bytearray)):
            # For raw bytes data
            uploaded_data = uploaded_image
        else:
            print(f"Error: Unsupported uploaded image type: {type(uploaded_image)}")
            return False
            
        uploaded_nparr = np.frombuffer(uploaded_data, np.uint8)
        uploaded_img = cv2.imdecode(uploaded_nparr, cv2.IMREAD_COLOR)
        
        # Reset file pointer for potential reuse if it's a file object
        if hasattr(uploaded_image, 'seek'):
            uploaded_image.seek(0)
        
        # Read stored image
        stored_img = cv2.imread(stored_image_path)
        
        if uploaded_img is None or stored_img is None:
            print("Error: Could not read one or both images")
            print(f"Uploaded image is None: {uploaded_img is None}")
            print(f"Stored image is None: {stored_img is None}")
            if stored_img is None:
                print(f"Stored image path: {stored_image_path}")
                print(f"Stored image exists: {os.path.exists(stored_image_path)}")
                if os.path.exists(stored_image_path):
                    print(f"Stored image size: {os.path.getsize(stored_image_path)}")
            return False
            
        # Convert to grayscale
        uploaded_gray = cv2.cvtColor(uploaded_img, cv2.COLOR_BGR2GRAY)
        stored_gray = cv2.cvtColor(stored_img, cv2.COLOR_BGR2GRAY)
        
        # Load Haar cascade for face detection
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Detect faces in both images
        uploaded_faces = face_cascade.detectMultiScale(
            uploaded_gray,
            scaleFactor=1.1,
            minNeighbors=5,  # Increased from 3 to 5 for more accurate detection
            minSize=(50, 50),  # Increased from (30, 30) for better quality faces
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        stored_faces = face_cascade.detectMultiScale(
            stored_gray,
            scaleFactor=1.1,
            minNeighbors=5,  # Increased from 3 to 5 for more accurate detection
            minSize=(50, 50),  # Increased from (30, 30) for better quality faces
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Check if faces are detected in both images
        if len(uploaded_faces) == 0:
            print("No faces detected in uploaded image")
            return False
            
        if len(stored_faces) == 0:
            print("No faces detected in stored image")
            return False
            
        # Use the largest face if multiple faces are detected
        uploaded_face_coords = max(uploaded_faces, key=lambda face: face[2] * face[3])  # Max by area (w*h)
        stored_face_coords = max(stored_faces, key=lambda face: face[2] * face[3])  # Max by area (w*h)
        
        # Extract face regions using the coordinates
        (x1, y1, w1, h1) = uploaded_face_coords
        (x2, y2, w2, h2) = stored_face_coords
        
        uploaded_face = uploaded_gray[y1:y1+h1, x1:x1+w1]
        stored_face = stored_gray[y2:y2+h2, x2:x2+w2]
        
        # Check if face regions are valid
        if uploaded_face.size == 0 or stored_face.size == 0:
            print("Invalid face regions extracted")
            return False
        
        # Resize faces to same size for comparison
        uploaded_face_resized = cv2.resize(uploaded_face, (100, 100))
        stored_face_resized = cv2.resize(stored_face, (100, 100))
        
        # Calculate histogram correlation as similarity measure
        hist1 = cv2.calcHist([uploaded_face_resized], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([stored_face_resized], [0], None, [256], [0, 256])
        
        # Normalize histograms
        hist1 = cv2.normalize(hist1, hist1).flatten()
        hist2 = cv2.normalize(hist2, hist2).flatten()
        
        correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        
        # Print debug information
        print(f"Face similarity correlation: {correlation}")
        print(f"Uploaded face size: {uploaded_face.shape}")
        print(f"Stored face size: {stored_face.shape}")
        
        # Return the actual correlation value, not a boolean
        # The face login function will handle the threshold comparison
        return correlation
    except Exception as e:
        print(f"Error in face comparison: {e}")
        import traceback
        traceback.print_exc()
        return False

@csrf_exempt
def face_login(request):
    """
    Handle face login functionality
    """
    logger.debug(f"Face login called with method: {request.method}")
    
    if request.method == 'POST':
        logger.debug(f"Files in request: {list(request.FILES.keys())}")
        logger.debug(f"POST data: {list(request.POST.keys())}")
        
        # Handle base64 encoded image from camera
        print(f"Received POST data keys: {list(request.POST.keys())}")
        print(f"Received FILES keys: {list(request.FILES.keys())}")
        image_data = request.POST.get('image')
        print(f"Image data present: {image_data is not None}")
        print(f"Image data length: {len(image_data) if image_data else 0}")
        if image_data and image_data.startswith('data:image'):
            logger.debug("Processing base64 encoded image")
            try:
                import base64
                import tempfile
                from django.core.files.uploadedfile import TemporaryUploadedFile
                
                # Decode base64 image
                image_data = request.POST.get('image')
                print(f"Full image data: {image_data[:100]}...")  # Print first 100 chars
                if ';base64,' in image_data:
                    format, imgstr = image_data.split(';base64,') 
                    ext = format.split('/')[-1] 
                    print(f"Format: {format}, Extension: {ext}")
                    print(f"Base64 data length: {len(imgstr)}")
                    
                    # Decode the image data
                    try:
                        img_data = base64.b64decode(imgstr)
                        print(f"Decoded image data length: {len(img_data)}")
                    except Exception as decode_error:
                        print(f"Error decoding base64 data: {decode_error}")
                        messages.error(request, f'Error decoding image data: {str(decode_error)}')
                        return render(request, 'recognition/face_login_camera.html')
                else:
                    print("Invalid image data format - missing base64 prefix")
                    messages.error(request, 'Invalid image data format.')
                    return render(request, 'recognition/face_login_camera.html')
                
                # Instead of creating a TemporaryUploadedFile, pass the raw bytes directly
                uploaded_image = img_data
                logger.debug(f"Created image data from base64: {len(img_data)} bytes")
            except Exception as e:
                logger.error(f"Error processing base64 image: {e}")
                messages.error(request, f'Error processing captured image: {str(e)}')
                return render(request, 'recognition/face_login_camera.html')
                
        # Handle uploaded file
        elif request.FILES.get('image'):
            logger.debug("Processing uploaded file")
            uploaded_image = request.FILES['image']
        else:
            logger.error("No image provided")
            messages.error(request, 'Please upload an image for face login.')
            return render(request, 'recognition/face_login_camera.html')
        
        try:
            # First, detect if there's a face in the uploaded image
            logger.debug("Detecting face in uploaded image...")
            print(f"Uploaded image type: {type(uploaded_image)}")
            if hasattr(uploaded_image, 'size'):
                print(f"Uploaded image size: {uploaded_image.size}")
            face_detected = detect_face_opencv(uploaded_image)
            logger.debug(f"Face detected: {face_detected}")
            print(f"Face detected result: {face_detected}")
            
            if not face_detected:
                messages.error(request, 'No face detected in the image. Please ensure your face is clearly visible, well-lit, centered, and try again. Make sure your entire face is within the camera frame.')
                return render(request, 'recognition/face_login_camera.html')
            
            # Reset file pointer after detection if it's a file object
            if hasattr(uploaded_image, 'seek'):
                uploaded_image.seek(0)
            
            # Compare with stored face records
            face_records = FaceRecord.objects.all()
            matched_user = None
            best_match_score = 0
            best_match_user = None
            
            logger.debug(f"Comparing with {face_records.count()} face records...")
            
            if face_records.count() == 0:
                messages.error(request, 'No face records found in the system. Please register your face first.')
                return render(request, 'recognition/face_login_camera.html')
            
            for record in face_records:
                # Check if the face record has an associated user profile
                try:
                    # Get user profile associated with this face record
                    user_profile = UserProfile.objects.get(face_record=record)
                    if user_profile and record.image:
                        # Get the full path to the stored image
                        stored_image_path = record.image.path
                        logger.debug(f"Comparing with record {record.id} for user {user_profile.user.username}")
                        
                        # Check if the stored image file exists and is not empty
                        if not os.path.exists(stored_image_path) or os.path.getsize(stored_image_path) == 0:
                            logger.warning(f"Stored image file does not exist or is empty: {stored_image_path}")
                            continue
                        
                        # Compare faces
                        similarity_score = compare_faces_opencv(uploaded_image, stored_image_path)
                        logger.debug(f"Similarity score with {user_profile.user.username}: {similarity_score}")
                        
                        # Keep track of the best match
                        # Make sure we're comparing numerical values, not boolean results
                        if isinstance(similarity_score, (int, float)) and similarity_score > best_match_score:
                            best_match_score = similarity_score
                            best_match_user = user_profile.user
                except Exception as e:
                    # Continue to next record if this one fails
                    logger.error(f"Error comparing with record {record.id}: {e}")
                    continue
            
            # Use threshold for matching
            logger.debug(f"Best match score: {best_match_score}")
            # Use a reasonable threshold of 0.7 for better accuracy
            if best_match_score > 0.7:
                matched_user = best_match_user
            
            if matched_user:
                logger.debug(f"Matched user: {matched_user.username}")
                # Log in the user
                login(request, matched_user)
                
                # Redirect based on user type
                try:
                    profile = UserProfile.objects.get(user=matched_user)
                    if profile.user_type == 'super_admin':
                        return redirect('recognition:super_admin_dashboard')
                    elif profile.user_type == 'franchise_owner':
                        return redirect('recognition:franchise_owner_dashboard')
                    else:
                        return redirect('recognition:user_dashboard')
                except Exception as e:
                    logger.error(f"Error accessing user profile: {e}")
                    messages.error(request, 'Error accessing user profile.')
                    return redirect('recognition:login')
            else:
                logger.debug("No matching user found")
                messages.error(request, f'Face not recognized. Please try again or use password login. (Best match score: {best_match_score:.2f})')
        except Exception as e:
            logger.error(f"Error during face login: {e}", exc_info=True)
            messages.error(request, f'Error during face login: {str(e)}')
    
    return render(request, 'recognition/face_login_camera.html')
