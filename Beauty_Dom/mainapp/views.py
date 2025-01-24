from django.http import HttpResponse
from django.views.generic import FormView, ListView, DetailView, TemplateView
from .models import *
from .forms import *
from .utils import *
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from django.shortcuts import get_object_or_404
from django.contrib.auth.views import LoginView
from Beauty_Dom.settings import START_WORK, END_WORK, BREAK_AFTER_WORK, WORKDAY_DURATION, is_verify
from datetime import timedelta, date, datetime
from decimal import Decimal
from django.contrib.auth.mixins import LoginRequiredMixin




#представление для регистрации
class CustomerSignUpView(FormView):
    form_class = CustomerSignUpForm
    template_name = 'mainapp/signup.html'

    def get_success_url(self):
        return reverse_lazy('success', kwargs={'source': 'signup'})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Извлекаем параметр source из URL
        context['source'] = self.kwargs.get('source')
        context['title'] = 'Регистрация'
        return context 
    
    def form_valid(self, form):
        if is_verify:
            user = form.save(commit=False)
            user.is_active = False  # деактивируем пользователя до подтверждения

            # Сохраняем email в сессию
            self.email = form.cleaned_data['email']
            self.request.session['email'] =  self.email 

            # Генерация уникального кода подтверждения
            user.verification_code = str(uuid.uuid4())  # Генерируем код
            user.save()

            # Отправка письма с кодом подтверждения
            verification_link = self.request.build_absolute_uri(
                reverse_lazy('verify', args=[user.verification_code])
            )

            send_activation_code(self.email, verification_link)
            return super().form_valid(form)
        else:
            user = form.save()
            return super().form_valid(form)

# представление для входа
class CustomerLoginView(LoginView):
    template_name = 'mainapp/login.html'
    form_class = CustomerLoginForm

    def get_success_url(self):
        return reverse_lazy('index')  # Указываете URL, на который нужно перенаправить

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Вход'
        return context

    def form_invalid(self, form):
        messages.error(self.request, "Пожалуйста, введите правильные имя пользователя и пароль.")
        return super().form_invalid(form)


# главная страница
class Index(TemplateView):
    template_name = 'mainapp/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Главная страница'
        return context
    
# стпаница о нас
class About(ListView):
    template_name = 'mainapp/about.html'
    model = ProfileEmployer
    context_object_name = 'profiles'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'О нас'
        return context

# страница отзывов  
class Reviews(ListView):
    template_name = 'mainapp/reviews.html'
    model = Review
    context_object_name = 'reviews'
    paginate_by = 15

    def get_queryset(self):
        return Review.objects.filter(is_approved=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Отзывы'
        context['total_rating'] = SiteRating.objects.first().total_rating
        context['total_reviews'] = SiteRating.objects.first().total_reviews
        return context
    
# страница для добавления отзыва
class AddReview(FormView):
    form_class = ReviewForm
    template_name = 'mainapp/add_review.html'
    success_url = reverse_lazy('reviews')


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Оставить отзыв'
        return context
    
    def form_valid(self, form):
        review = form.save(commit=False)  # Сохраняем форму, но не отправляем в базу
        review.user = self.request.user  # Присваиваем текущего пользователя
        review.save()  # Сохраняем отзыв с пользователем
        return super().form_valid(form)

# Записи пользователя
class MyAppointments(LoginRequiredMixin, ListView):
    template_name = 'mainapp/userappointment.html'
    model = Appointment

    def get(self, request):
        current_user = self.request.user
        current_client = Client.objects.get(user=current_user)
        my_appointments = self.model.objects.filter(client=current_client, status='not_complete')
        return render(request, self.template_name, {'my_appointments': my_appointments})
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Мои записи'
        return context

# Страница пользователя
class ProfileUser(LoginRequiredMixin, ListView):
    template_name = 'mainapp/profileuser.html'
    model = CustomUser

    def get(self, request):
        return render(request, self.template_name, {'user': request.user})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Профиль'
        return context

# предназначена для удаления учетной записи пользователя
@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, "Ваш аккаунт был успешно удален.")  # Сообщение об успехе
        return redirect('index')
    
    return render(request, 'confirm_delete.html')  # Отображаем страницу подтверждения

# представление ферификации
class VerifyUserView(View):
    def get(self, request, code):
        user = get_object_or_404(CustomUser, verification_code=code)
        if not user.is_active:
            user.is_active = True
            Client.objects.get_or_create(user=user)
            user.save()
        return redirect('login', permanent=True)  # Перенаправление на страницу входа

# представления для записи / несколько шагов
class AppointmentViewStep1(FormView):
    template_name = 'mainapp/appointment1.html'

    def return_to_page(self, request, error_message=None):
        services = Service.objects.all()

        if error_message:
            return render(request, self.template_name, {'services': services, 'error_message': error_message})  
          
        return render(request, self.template_name, {'services': services})
            
    def get(self, request):
        return self.return_to_page(request)

    def post(self, request):

        selected_services_ids = self.request.POST.getlist('services')

        if not selected_services_ids:
            self.return_to_page(request, 'Пожалуйста, выберите хотя бы одну услугу.')

        total_time = calculate_total_time(selected_services_ids)
        if total_time >= WORKDAY_DURATION:
            self.return_to_page(request, 'Длительность выбранных услуг превышает рабочий день.')

        # Доступные даты
        available_dates = get_available_dates(selected_services_ids)

        # Сохранение в сессии
        self.request.session['selected_services_ids'] = selected_services_ids
        self.request.session['available_dates'] = [date.isoformat() for date in available_dates]


        return redirect('appointment_step2')


class AppointmentViewStep2(FormView):
    template_name = 'mainapp/appointment2.html'

    def get(self, request):
        available_dates = self.request.session.get('available_dates')
        form = DateForm
        return render(request, self.template_name, {'form': form, 'available_dates': available_dates})

    def post(self, request):

        form = DateForm(request.POST)
        if form.is_valid():
            
            total_time = calculate_total_time(self.request.session.get('selected_services_ids'))
            selected_date = str(form.cleaned_data['date'])
            available_start_time = get_available_start_time(selected_date, total_time)

            self.request.session['selected_date'] = selected_date
            self.request.session['available_start_time'] = available_start_time

            return redirect('appointment_step3')
    
        available_dates = self.request.session.get('available_dates')
        form = DateForm
        return render(request, self.template_name, {'form': form, 'availeble_dates': available_dates})


   
class AppointmentViewStep3(FormView):
    template_name = 'mainapp/appointment3.html'
    form_class = StartTimeForm
    
    def get_choices(self):
        available_start_time = self.request.session.get('available_start_time')
        choices = [(i, i) for i in available_start_time]
        return choices

    def return_to_page(self, request, form=None):
        form = self.form_class(self.request.POST or None, choices=self.get_choices())
        title = 'Заптсь на прием'
        return render(request, self.template_name, {'form': form, 'title': title})
    

    def get(self, request):
        return self.return_to_page(request)
    

    def post(self, request):
        form = StartTimeForm(request.POST, choices=self.get_choices())

        if form.is_valid():
            self.request.session['selected_start_time'] = str(form.cleaned_data['start_time']) 
            return redirect('appointment_step4')

        return self.return_to_page(request, form)

    
class AppointmentViewStep4(FormView):
    template_name = 'mainapp/appointment4.html'


    def all_need_params_in_session(self, request):
        selected_date, selected_services_ids, selected_start_time = self.get_data(request)
        return {
            'selected_start_time': selected_start_time,
            'selected_services': get_service_names(selected_services_ids),
            'selected_date': selected_date,
            'total_time': calculate_total_time(selected_services_ids), 
            'total_price': calculate_total_price(selected_services_ids),
            'end_time': calculate_end_time(selected_start_time, calculate_total_time(selected_services_ids))
        }

    def get_data(self, request):
        return (self.request.session.get('selected_date'), 
            self.request.session.get('selected_services_ids'),
            self.request.session.get('selected_start_time')       
        )
    
    def get(self, request):
        params = self.all_need_params_in_session(request)
        return render(request, self.template_name, params)
    
    def post(self, request):
        params = self.all_need_params_in_session(request)
        appointment = Appointment.objects.create(
            client=Client.objects.get(user=self.request.user),
            date=params['selected_date'],
            start_time=params['selected_start_time'],
            end_time=params['end_time'],
            total_price = params['total_price'],
            status='not_complete'
        )
        for name in params['selected_services']:
            service = Service.objects.get(name=name)  # Или get_or_create
            appointment.services.add(service)

        appointment.save
        return HttpResponse('<h1>готово</h1>')

    
# страница для завершения регистрации
class Success(TemplateView):
    template_name = 'mainapp/success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Подтвердите почту'
        context['email'] = self.request.session.get('email', '|не указано|')
        return context


class RecoverPasswordStep1(FormView):
    template_name = 'mainapp/recover_password1.html'
    form_class = RecoverPasswordFormStep1

    def get_success_url(self):
        return reverse_lazy('success', kwargs={'source': 'recover_password1'})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Извлекаем параметр source из URL
        context['source'] = self.kwargs.get('source')
        context['title'] = 'Востановить пароль'
        return context
    
    def form_valid(self, form) -> HttpResponse:
        
        # Сохраняем email в сессию
        self.email = form.cleaned_data['email']
        self.request.session['email'] = self.email

        try:
            user = CustomUser.objects.get(email=self.email)
            verification_code = str(uuid.uuid4())
            user.verification_code = verification_code
            user.save()
            # Отправка письма с кодом подтверждения
            verification_link = self.request.build_absolute_uri(
                reverse_lazy('recover_password2', args=[verification_code])
            )

            send_recover_link(self.email, verification_link)

            return super().form_valid(form)
        except CustomUser.DoesNotExist:
            pass


        return super().form_valid(form)

    

class RecoverPasswordStep2(FormView):
    template_name = 'mainapp/recover_password2.html'
    form_class = RecoverPasswordFormStep2

    def get_success_url(self):
        return reverse_lazy('login')

    def get_context_data(self, **kwargs):   
        context = super().get_context_data(**kwargs)
        context['title'] = 'Введите новый пароль'
        context['code'] = self.kwargs.get('code')
        return context
    
    def form_valid(self, form) -> HttpResponse:
        password1 = form.cleaned_data['password1']
        password2 = form.cleaned_data['password2']

        if password1 == password2:
            code = self.kwargs.get('code')
            user = CustomUser.objects.get(verification_code=code)
            # Установка нового пароля
            user.set_password(password1)
            user.save()
            return super().form_valid(form)
        else:
            messages.error(self.request, 'Пароли не совпадают')
            return super().form_invalid(form)




























