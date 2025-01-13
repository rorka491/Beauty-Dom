from django.contrib import admin
from .models import *
from django.forms import DateTimeInput
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django import forms


class ClientRecordForm(forms.ModelForm):
    """"""
    class Meta:
        model = Appointment
        fields = '__all__'
        exclude = ['total_price', 'total_time', 'end_time', 'end_time_after_break', 'status', 'session_key']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Устанавливаем профиль по умолчанию для неавторизованных пользователей
        self.fields['user'].initial = CustomUser.objects.get(username='Nadezhda')



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
    list_display = ('user__first_name', 'user__last_name', 'start_time', 'end_time', 'date', 'total_price','name', 'last_name', 'phone_number', 'status')
    form = ClientRecordForm


class ReviewsAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_approved']

admin.site.register(Service, ServiceAdmin)
admin.site.register(ProfileEmployer)
admin.site.register(Review, ReviewsAdmin)
admin.site.register(SiteRating)
admin.site.register(CustomUser, UserAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(NotAvailaibleDates)




