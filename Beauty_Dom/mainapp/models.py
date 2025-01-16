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
        total_rating = Review.objects.aggregate(average_rating=Avg('rating'))
        total_reviews = Review.objects.count()
        
        self.total_rating = total_rating['average_rating'] or 0
        self.total_reviews = total_reviews
        self.save()



class Appointment(models.Model):
    import utils

    class Meta: 
        verbose_name = 'Запись на прием'  # Измените на нужное название
        verbose_name_plural = 'Записи на прием'  # Измените на нужное множественное число
        ordering = ['-status']
        

    CHOICES = [
        ('complete', 'ЗАВЕРШЕНО'),
        ('not_complete', 'НЕ ЗАВЕРШЕНО')
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    services = models.ManyToManyField(Service)
    notes = models.CharField(max_length=2000, blank=True)
    total_price = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_time = models.DurationField(default=timedelta(0))  # Хранит общее время
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    end_time_after_break = models.TimeField()
    status = models.CharField(choices=CHOICES, default='not_complete', max_length=12)
    session_key = models.CharField(max_length=40, null=True, blank=True)  # Хранение ключа сессии для связи

    name = models.CharField(max_length=40, blank=True)
    last_name = models.CharField(max_length=40, blank=True)
    phone_number = models.CharField(max_length=11, blank=True)



    def calculate_total_price(self, services):
        return sum(service.price for service in services)   

    def calculate_total_time(self, services):
        total_time = timedelta()  # Инициализация начальным значением
        for service in services:
            total_time += service.time  # Сложение каждого duration
        return total_time
    
    def add_time_and_timedelta(self, t: time, delta: timedelta, delta_break: timedelta) -> time:
        datetime_obj1 = datetime.combine(datetime.min, t) + delta
        datetime_obj2 = datetime_obj1 + delta_break
        return datetime_obj1.time(), datetime_obj2.time()
    
    def save(self, *args, **kwargs):
        # Проверяем, создается ли объект впервые
        is_new = self.pk is None

        # Сохраняем объект, чтобы он получил ID
        super().save(*args, **kwargs)

        # Выполняем расчеты только после получения ID
        if self.services.exists() or is_new:
            self.total_price = self.calculate_total_price(self.services.all())
            self.total_time = self.calculate_total_time(self.services.all())
            self.end_time, self.end_time_after_break = self.add_time_and_timedelta(
                self.start_time, self.total_time, BREAK_AFTER_WORK
            )
            # Сохраняем изменения, указав только измененные поля
            super().save(update_fields=['total_price', 'total_time', 'end_time', 'end_time_after_break'])

        
class NotAvailaibleDates(models.Model):
    date = models.DateField()

    class Meta:
        verbose_name = 'недоступную дату'
        verbose_name_plural = 'Недоступные даты'

    def __str__(self):
        return f'{self.date}'














