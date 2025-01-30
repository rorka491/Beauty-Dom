from django.contrib import admin
from .models import *
from django.forms import DateTimeInput
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django import forms
from django.utils.html import format_html



class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'surname')


class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'time', 'price', 'service_type')  # Поля, которые будут отображаться в списке
    search_fields = ('name',)  # Поля для поиска
    list_filter = ('price',)  # Фильтры по полям

    
class UserAdmin(BaseUserAdmin):

    # Поля, которые будут отображаться в списке
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'verification_code', 'picture_user')

    # Поля для редактирования в форме
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('verification_code', 'picture_user')}),
    )

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client__name', 'client__last_name', 'start_time', 'end_time', 'date', 'total_price', 'status', 'display_services')

class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'last_name', 'phone_number', 'user__username']


@admin.register(Review)
class ReviewsAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_approved']

class BlogPostPhotosInline(admin.TabularInline):  # Можно заменить на StackedInline для другого стиля
    model = BlogPostPhotos
    extra = 1  # Количество пустых полей для добавления новых записей
    fields = ('photo',)  # Поля, доступные для редактирования



@admin.register(BlogPost)
class CategotyAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    inlines = [BlogPostPhotosInline] 



@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "discount", "expires_at", "is_active")
    actions = ["generate_promo_codes"]
    
    
    @admin.action(description='Создать 10 промокодов')
    def generate_codes(self, request, queryset):
        from datetime import date
        from .models import Service

        services = Service.objects.all()[:3]  # Применить к первым 3 сервисам
        PromoCode.generate_codes(count=10, discount=10.0, expires_at=date(2025, 12, 31), services=services)

        self.message_user(request, "Создано 10 промокодов!")

    def create_promo_codes_button(self, request):
        return format_html(
            '<a class="button" href="{}">Создать 12 промокодов</a>',
            "generate_promo_codes"
    )

    create_promo_codes_button.allow_tags = True
    create_promo_codes_button.short_description = "Создать 12 промокодов"
    







admin.site.register(Service, ServiceAdmin)
admin.site.register(ProfileEmployer)
# admin.site.register(Review, ReviewsAdmin)
admin.site.register(SiteRating)
admin.site.register(CustomUser, UserAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(NotAvailaibleDates)
admin.site.register(Client, ClientAdmin)
admin.site.register(VideoFile)
admin.site.register(BlogPostPhotos)
admin.site.register(BlogPostComment)






