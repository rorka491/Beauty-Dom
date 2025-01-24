from django.urls import path
from mainapp.views import *
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views
from adminapp.views import AppointmentViewStep1, AppointmentViewStep2, AppointmentViewStep3, AppointmentViewStep4


urlpatterns = [
    path('form_step1/', AppointmentViewStep1.as_view(), name='form_step1'),
    path('form_step2/', AppointmentViewStep2.as_view(), name='form_step2'),
    path('form_step3/', AppointmentViewStep3.as_view(), name='form_step3'),
    path('form_step4/', AppointmentViewStep4.as_view(), name='form_step4'),
]



