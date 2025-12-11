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
import numpy as np
import cv2

def debug_face_login():
    print("Debugging face login functionality...")
    print("=" * 50)
    
    try:
        # Get the face record
        face_record = FaceRecord.objects.get(id=2)
        print(f"Found face record: {face_record.name}")
        print(f"Image path: {face_record.image.path}")
        
        # Check if file exists
        if os.path.exists(face_record.image.path):
            print("Image file exists")
        else:
            print("Image file does not exist!")
            return
            
        # Try to read the image
        img = cv2.imread(face_record.image.path)
        if img is not None:
            print(f"Image loaded successfully. Shape: {img.shape}")
        else:
            print("Failed to load image!")
            return
            
        # Test face detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        print(f"Faces detected: {len(faces)}")
        
        if len(faces) > 0:
            print("Face detection working correctly")
        else:
            print("No faces detected in stored image")
            
        # Test the comparison function
        from recognition.views import compare_faces_opencv
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Create a simple uploaded file from the same image
        with open(face_record.image.path, 'rb') as f:
            image_data = f.read()
        
        uploaded_file = SimpleUploadedFile(
            name='test_face.jpg',
            content=image_data,
            content_type='image/jpeg'
        )
        
        # Test face comparison
        similarity = compare_faces_opencv(uploaded_file, face_record.image.path)
        print(f"Face similarity score: {similarity}")
        
        if similarity:
            print("Face comparison working")
        else:
            print("Face comparison failed")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_face_login()