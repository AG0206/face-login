# Smart Library System

A modern digital library system with multi-login and face recognition capabilities.

## Features

### Authentication System
- **Super Admin (HQ)**: Full system access to manage all franchises, users, and books
- **Franchise Owner**: Manage their own franchise including books and users
- **User/Student**: Access personal dashboard to issue/return books and manage profile

### Registration
- User registration with franchise selection
- Franchise owner registration with franchise creation
- Face recognition registration (optional)

### Dashboards
- **Super Admin Dashboard**: System-wide statistics and reports
- **Franchise Owner Dashboard**: Franchise-specific management
- **User Dashboard**: Personal book management

### Book Management
- Add, edit, and delete books (franchise owners only)
- Search and browse books
- Issue and return books
- Track book availability

### User Management
- Super Admin can reset passwords for any user
- View all users in the system
- User type differentiation

### Face Recognition
- Optional face recognition login
- Face registration for users

## System Architecture

### Models
1. **Franchise**: Represents a library branch
2. **UserProfile**: Extended user profile with user type and franchise association
3. **Book**: Library books with franchise association
4. **BookIssue**: Track book issues and returns

### User Types
- **super_admin**: System administrator with full access
- **franchise_owner**: Franchise manager
- **student**: Regular user/student

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run migrations:
   ```
   python manage.py migrate
   ```
4. Create a superuser:
   ```
   python manage.py createsuperuser
   ```
5. Run the development server:
   ```
   python manage.py runserver
   ```

## Usage

1. Access the application at `http://127.0.0.1:8000/`
2. Register as a franchise owner or user
3. Log in with your credentials
4. Use the appropriate dashboard based on your user type

### Login Process
- Users are automatically redirected to their respective dashboards based on their user type
- If a user profile is missing, the system will attempt to create one automatically
- Super admins are identified by the 'admin' keyword in their username or by being the first user

### Super Admin Password Reset
As a Super Admin:
1. Navigate to the Super Admin Dashboard
2. Scroll to the "User Management" section
3. Find the user whose password you want to reset
4. Click the "Reset Password" button next to their name
5. Enter a new password and confirm it
6. The user's password will be updated immediately

## Future Enhancements

- Notification system (due dates, new books)
- Book transfer requests between franchises
- Mobile app with camera integration for face login
- Reports & analytics (franchise growth, active users)

## Technologies Used

- Django (Web framework)
- SQLite (Database)
- HTML/CSS/JavaScript (Frontend)
- Font Awesome (Icons)