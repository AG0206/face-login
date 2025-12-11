from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create a UserProfile when a User is created
    """
    if created:
        # For super admin user (first user or users with 'admin' in username)
        if User.objects.count() == 1 or 'admin' in instance.username.lower():
            UserProfile.objects.create(
                user=instance,
                user_type='super_admin'
            )
        else:
            # For other users, create a default student profile
            # This is a fallback for users created outside the registration forms
            try:
                UserProfile.objects.create(
                    user=instance,
                    user_type='student'
                )
            except Exception:
                # If there's any issue, we'll handle it in the login view
                pass

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the UserProfile when a User is saved
    """
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()