import os
import sys
import django
from django.conf import settings

# Add the project directory to the Python path
sys.path.append('D:/Facelog')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facelog.settings')

# Setup Django
django.setup()

# Now we can import Django models
from recognition.models import FaceRecord, UserProfile
from django.contrib.auth.models import User

def check_face_records():
    print("Checking Face Records in Database...")
    print("=" * 50)
    
    # Check all face records
    face_records = FaceRecord.objects.all()
    print(f"Total Face Records: {face_records.count()}")
    
    for record in face_records:
        print(f"\nID: {record.id}")
        print(f"Name: {record.name}")
        print(f"Image: {record.image}")
        print(f"Created: {record.created_at}")
        print(f"Updated: {record.updated_at}")
    
    print("\n" + "=" * 50)
    print("Checking User Profiles with Face Records...")
    print("=" * 50)
    
    # Check user profiles with face records
    profiles_with_faces = UserProfile.objects.exclude(face_record=None)
    print(f"User Profiles with Face Records: {profiles_with_faces.count()}")
    
    for profile in profiles_with_faces:
        print(f"\nUser: {profile.user.username}")
        print(f"Face Record: {profile.face_record.name if profile.face_record else 'None'}")
        if profile.face_record:
            print(f"Image Path: {profile.face_record.image}")

if __name__ == "__main__":
    try:
        check_face_records()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()