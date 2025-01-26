from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db.models import Avg
from datetime import datetime, timedelta, time
from Beauty_Dom.settings import BREAK_AFTER_WORK


# Create your models here.
class CustomUser(AbstractUser):
    verification_code = models.CharField(max_length=100, blank=True, null=True)
    # picture_user = models.ImageField(upload_to= )

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',  # Измените имя здесь
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',  # Измените имя здесь
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )


class Client(models.Model):
    user = models.OneToOneField(CustomUser, null=True, blank=True, on_delete=models.CASCADE)

    phone_number = models.CharField(max_length=11, blank=True, null=True)
    name = models.CharField(max_length=255,)
    last_name = models.CharField(max_length=255,)

    # Дополнительные поля для всех клиентов
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'клиенты'


    def __str__(self):
        return self.user.username if self.user else self.name
    
class Service(models.Model):
    CHOICES_TYPE = [
        ('manicure', 'маникюр'),
        ('pedicure', 'педикюр'),
        ('face', 'лицо'),
        ('piling', 'пилинг')  
    ]

    name = models.CharField(max_length=200, blank=False)
    time = models.DurationField(default='00:00:00')
    price = models.DecimalField(max_digits=20, decimal_places=0, blank=False)
    image = models.ImageField(upload_to='mom_site/mainapp/static/mainapp/images', null=True, blank=True)
    service_type = models.CharField(max_length=40, choices=CHOICES_TYPE, default='manicure')
    note_service = models.TextField(blank=True)
    

    class Meta:
        verbose_name = 'Услуга'  # Измените на нужное название
        verbose_name_plural = 'Услуги'  # Измените на нужное множественное число

    def __str__(self):
        return self.name
    


class ProfileEmployer(models.Model):
    head = models.CharField(max_length=40)
    text = models.CharField(max_length=400)
    image = models.ImageField(upload_to='profiles/')
    

    class Meta:
        verbose_name = 'Работник'  # Измените на нужное название
        verbose_name_plural = 'Работники'  # Измените на нужное множественное число

    def __str__(self):
        return f'Описание {self.head}'


class Review(models.Model):

    CHOICES = [
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    ]


    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    notes = models.TextField()
    rating = models.IntegerField(choices=CHOICES, default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Отзыв'  # Измените на нужное название
        verbose_name_plural = 'Отзывы'  # Измените на нужное множественное число

    def __str__(self):
        return f"Отзыв от {self.user.username} - {self.rating}/5"
    

class SiteRating(models.Model):
    total_rating = models.FloatField(default=0.0, )
    total_reviews = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Рейтинг сайта'  # Измените на нужное название
        verbose_name_plural = 'Рейтинг сайта'  # Измените на нужное множественное число

    def __str__(self):
        return f"Рейтинг: {self.total_rating} (Всего отзывов: {self.total_reviews})"

    @classmethod
    def get_instance(cls):
        instance, created = cls.objects.get_or_create(id=1)
        return instance
    
    def update_rating(self):
        # Обновляем рейтинг и количество отзывов
        total_rating = Review.objects.filter(is_approved=True).aggregate(average_rating=Avg('rating'))
        total_reviews = Review.objects.count()
        
        self.total_rating = total_rating['average_rating'] or 0
        self.total_reviews = total_reviews
        self.save()



class Appointment(models.Model):


    class Meta: 
        verbose_name = 'Запись на прием'  # Измените на нужное название
        verbose_name_plural = 'Записи на прием'  # Измените на нужное множественное число
        ordering = ['-status']
        
    CHOICES = [
        ('complete', 'ЗАВЕРШЕНО'),
        ('not_complete', 'НЕ ЗАВЕРШЕНО')
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    services = models.ManyToManyField(Service)
    notes = models.CharField(max_length=2000, blank=True)
    total_price = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_time = models.DurationField(default=timedelta(0))  # Хранит общее время
    date = models.DateField(null=True)
    start_time = models.TimeField(null=True)
    end_time = models.TimeField(null=True)
    end_time_after_break = models.TimeField(null=True)
    status = models.CharField(choices=CHOICES, default='not_complete', max_length=12)
    session_key = models.CharField(max_length=40, null=True, blank=True)  # Хранение ключа сессии для связи

    def display_services(self):
        return ', '.join([service.name for service in self.services.all()]) 
    
    display_services.short_description = 'Услуги'



        
class NotAvailaibleDates(models.Model):
    date = models.DateField()

    class Meta:
        verbose_name = 'недоступную дату'
        verbose_name_plural = 'Недоступные даты'

    def __str__(self):
        return f'{self.date}'


class VideoFile(models.Model):
    title = models.CharField(
        max_length=100, 
        verbose_name='Описание файла',
        )

    file = models.FileField(
        upload_to='videos',
        verbose_name='Файл с видео',
        null=True, blank=True
        )
    
    class Meta:
        verbose_name = 'Видео'
        verbose_name_plural = 'Видео'

    obj_video = models.Manager()

    def __str__(self):
        return self.title







