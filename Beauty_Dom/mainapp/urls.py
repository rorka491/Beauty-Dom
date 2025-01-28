from django.urls import path
from mainapp.views import *
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views



urlpatterns = [
    path('', Index.as_view(), name='index'),
    path('delete_video/<int:id>/', delete_video, name='delete_video'),
    path('about/', About.as_view(), name='about'),
    path('reviews/', Reviews.as_view(), name='reviews'),
    path('success/<str:source>/', Success.as_view(), name='success'),
    path('add_review/', AddReview.as_view(), name='add_review'),
    path('login/', CustomerLoginView.as_view(), name='login'),
    path('signup/', CustomerSignUpView.as_view(), name='signup'),
    path('profileuser/', ProfileUser.as_view(), name='profileuser'),
    path('my_appointments/', MyAppointments.as_view(), name='my_appointments'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('verify/<uuid:code>/', VerifyUserView.as_view(), name='verify'),
    path('delete_account/', delete_account, name='delete_account'),
    path('appointment_step1/', AppointmentViewStep1.as_view(), name='appointment_step1'),
    path('appointment_step2/', AppointmentViewStep2.as_view(), name='appointment_step2'),
    path('appointment_step3/', AppointmentViewStep3.as_view(), name='appointment_step3'),
    path('appointment_step4/', AppointmentViewStep4.as_view(), name='appointment_step4'),
    path('recover_password1/', RecoverPasswordStep1.as_view(), name='recover_password1'),
    path('recover_password2/<uuid:code>/', RecoverPasswordStep2.as_view(), name='recover_password2'),
    path('blog_post/<slug:slug>', BlogPostView.as_view(), name='blog_post')
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


    