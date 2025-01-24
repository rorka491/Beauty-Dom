from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Review, SiteRating
from django.contrib.sessions.models import Session
from django.db.models.signals import post_delete
from django.utils import timezone
from .models import Review, Appointment, Service
from .utils import calculate_end_time, calculate_total_price, calculate_total_time
from .models import CustomUser, Client


@receiver(post_save, sender=Review)
def update_site_rating(sender, instance, **kwargs):
    site_rating, _ = SiteRating.objects.get_or_create(id=1)  # Предполагается, что только один экземпляр SiteRating
    site_rating.update_rating()



@receiver(post_delete, sender=Review)
def update_site_rating_on_delete(sender, instance, **kwargs):
    site_rating, _ = SiteRating.objects.get_or_create(id=1)  # Предполагается, что только один экземпляр SiteRating
    site_rating.update_rating()



@receiver(post_save, sender=CustomUser)
def create_client_profile(sender, instance, created, **kwargs):
    if created:
        Client.objects.create(
            user = instance,
            name = instance.first_name,
            last_name = instance.last_name                  
        )







