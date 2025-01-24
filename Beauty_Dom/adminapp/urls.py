from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views
from adminapp.views import *


urlpatterns = [
    path('form_step1/', AdminAppointmentViewStep1.as_view(), name='form_step1'),
    path('form_step2/', AdminAppointmentViewStep2.as_view(), name='form_step2'),
    path('form_step3/', AdminAppointmentViewStep3.as_view(), name='form_step3'),
    path('form_step4/', AdminAppointmentViewStep4.as_view(), name='form_step4'),
]



