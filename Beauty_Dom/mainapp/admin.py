from django.contrib import admin
from .models import *
from django.forms import DateTimeInput
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django import forms




class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'surname')


class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'time', 'price', 'service_type')  # Поля, которые будут отображаться в списке
    search_fields = ('name',)  # Поля для поиска
    list_filter = ('price',)  # Фильтры по полям

    
class UserAdmin(BaseUserAdmin):

    # Поля, которые будут отображаться в списке
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'verification_code',)

    # Поля для редактирования в форме
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('verification_code',)}),
    )

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client__name', 'client__last_name', 'start_time', 'end_time', 'date', 'total_price', 'status')

class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'last_name', 'phone_number', 'user__username']

class ReviewsAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_approved']

admin.site.register(Service, ServiceAdmin)
admin.site.register(ProfileEmployer)
admin.site.register(Review, ReviewsAdmin)
admin.site.register(SiteRating)
admin.site.register(CustomUser, UserAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(NotAvailaibleDates)
admin.site.register(Client, ClientAdmin)




