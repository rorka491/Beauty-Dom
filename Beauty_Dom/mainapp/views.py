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
from django.shortcuts import render, redirect, get_object_or_404
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

    def form_invalid(self, form, *args, **kwargs):
        if 'username' in form.errors:
            messages.error(self.request, "Пользователь с таким именем не найден.")
        elif 'password' in form.errors:
            messages.error(self.request, "Неправильный пароль.")
        else:
            messages.error(self.request, "Пожалуйста, введите правильные имя пользователя и пароль.")

        return super().form_invalid(form)


# главная страница
class Index(ListView):
    template_name = 'mainapp/index.html'

    def get(self, request,):
        my_text = 'Загружаемые файлы'
        form = VideoForm()
        services = Service.objects.all()
        file_obj = VideoFile.obj_video.all()
        context = {'my_text': my_text, 'form': form,'file_obj': file_obj, 'services': services}
        return render(request, self.template_name, context)

    def post(self, request):
        form = VideoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
        my_text = 'Загружаемые файлы'

        form = VideoForm()
        file_obj = VideoFile.obj_video.all()
        context = {'my_text': my_text, 'form': form, 'file_obj': file_obj}
        return render(request, self.template_name, context)


def delete_video(request, id):
    video = VideoFile.obj_video.get(id=id)
    video.delete()
    return redirect('index')

# стпаница о нас
class About(ListView):
    template_name = 'mainapp/about.html'

    def get(self, request,):
        blog_posts = BlogPost.objects.prefetch_related('photos')
        profiles = ProfileEmployer.objects.all()

        context = {'title': 'О нас', 'blog_posts': blog_posts, 'profiles': profiles}
        return render(request, self.template_name, context)

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
    
    
class BlogPostView(DetailView):
    template_name = 'mainapp/blog_post.html'
    model = BlogPost

    def get(self, request, slug):
        post = BlogPost.objects.get(slug=slug)
        post_photos = BlogPostPhotos.objects.filter(blog_post=post)
        post_comments = BlogPostComment.objects.filter(blog_post=post)
        form = CommentForm()
        return render(request, self.template_name, {'post': post, 
                                                    'post_photos': post_photos, 
                                                    'post_comments': post_comments, 
                                                    'form': form})
    

    def post(self, request, slug):
        form = CommentForm(request.POST)
        post = BlogPost.objects.get(slug=slug)
        if form.is_valid():
            # Создаем новый комментарий
            comment = form.save(commit=False)
            comment.blog_post = post
            comment.author = request.user  # Привязываем комментарий к текущему пользователю
            comment.save()
        
        # После добавления комментария, перезагружаем страницу с обновленными данными   
        post_photos = BlogPostPhotos.objects.filter(blog_post=post)
        post_comments = BlogPostComment.objects.filter(blog_post=post)
        form = CommentForm()
        return render(request, self.template_name, {'post': post, 
                                                    'post_photos': post_photos, 
                                                    'post_comments': post_comments, 
                                                    'form': form})

    
def delete_appointment(reuquest, id):
    appointment = Appointment.objects.get(id=id)
    appointment.delete()
    return redirect('profile_user')



# Страница пользователя
class ProfileUser(LoginRequiredMixin, ListView):
    template_name = 'mainapp/profile_user.html'
    model = CustomUser

    def get(self, request):
        user_data = self.model.objects.get(id=self.request.user.id)
        current_user = self.request.user
        current_client = Client.objects.get(user=current_user)
        my_appointments = Appointment.objects.filter(client=current_client, status='not_complete').order_by('date', 'start_time')
        return render(request, self.template_name, {'user': request.user, 'user_data': user_data, 'my_appointments': my_appointments })
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Профиль'
        return context
    
class ProfileSuperUser(LoginRequiredMixin, TemplateView):
    template_name = 'mainapp/profile_superuser.html'

    def get(self, request):
        return render(request, self.template_name, {'user': request.user})


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
class BaseAppointmentViewStep(FormView):
    def get_session_data(self, keys):
        if isinstance(keys, str):
            return self.request.session.get(keys)
        
        return {key: self.request.session.get(key) for key in keys}
    

    def save_session_data(self, data):
        for key, value in data.items():
            self.request.session[key] = value


class AppointmentViewStep1(BaseAppointmentViewStep):
    template_name = 'mainapp/appointment1.html'


    def render_page(self, request, error_messages=None):
        services = Service.objects.all().order_by('service_type')
        step_text = 'Выберите услугу'
        step_count = 1


        context = {'services': services, 'step_text': step_text, 'step_count': step_count}
        if error_messages:
            context['error_messages'] = [error_messages]

        return render(request, self.template_name, context)
            
    def get(self, request):
        return self.render_page(request)

    def post(self, request):

        selected_services_ids = self.request.POST.getlist('services')

        if not selected_services_ids:
            return self.render_page(request, 'Пожалуйста, выберите хотя бы одну услугу.')

        total_time = calculate_total_time(selected_services_ids)
        if total_time >= WORKDAY_DURATION:
            return self.render_page(request, 'Длительность выбранных услуг превышает рабочий день.')

        # Доступные даты
        available_dates, available_dates_times = Day.create_available_list_days(30, calculate_total_time(selected_services_ids))

        self.save_session_data({'available_dates': available_dates,
                                'selected_services_ids': selected_services_ids,
                                'available_dates': available_dates,
                                'available_dates_times': available_dates_times})


        return redirect('appointment_step2')


class AppointmentViewStep2(BaseAppointmentViewStep):
    template_name = 'mainapp/appointment2.html'
    form_class = DateForm

    def render_page(self, request, error_messages=None):
        available_dates = self.get_session_data('available_dates')
        form = self.form_class
        step_text = 'Выберите день'
        step_count = 2


        context = {'form': form, 'available_dates': available_dates, 'step_text': step_text, 'step_count': step_count}
        # if error_messages:
        #     context[error_messages] = [error_messages]
        return render(request, self.template_name, {'form': form,
                                                    'available_dates': available_dates,
                                                    'step_text': step_text,
                                                    'step_count': step_count})

    def get(self, request):
        return self.render_page(request)

    def post(self, request):

        form = DateForm(request.POST)

        if form.is_valid():
            selected_date = str(form.cleaned_data['date'])

            self.save_session_data({'selected_date': selected_date})

            return redirect('appointment_step3')

        return self.render_page(request)


   
class AppointmentViewStep3(BaseAppointmentViewStep):
    template_name = 'mainapp/appointment3.html'
    form_class = StartTimeForm
    
    def get_choices(self):
        selected_date = self.get_session_data('selected_date')
        available_dates_times = self.get_session_data('available_dates_times')
        available_start_times = available_dates_times[selected_date] 

        choices = [(i, i) for i in available_start_times]
        return choices

    def render_page(self, request, form=None):
        form = self.form_class(self.request.POST or None, choices=self.get_choices())
        step_text = 'Выберите время'
        step_count = 3
        return render(request, self.template_name, {'form': form,
                                                    'step_text': step_text,
                                                    'step_count': step_count})
    

    def get(self, request):
        return self.render_page(request)
    

    def post(self, request):
        form = self.form_class(request.POST, choices=self.get_choices())

        if form.is_valid():
            self.save_session_data({'selected_start_time': str(form.cleaned_data['start_time'])})
            return redirect('appointment_step4')

        return self.render_page(request, form)

    
class AppointmentViewStep4(BaseAppointmentViewStep):
    template_name = 'mainapp/appointment4.html'

    def render_page(self, request):
        params = self.all_need_params_in_session(request)
        params['step_text'] = 'Подтвердите запись'
        params['step_count'] = 4
        return render(request, self.template_name, params)

    def all_need_params_in_session(self, request):
        session_data = self.get_session_data(['selected_date', 'selected_services_ids', 'selected_start_time', 'total_time'])

        total_time = calculate_total_time(session_data['selected_services_ids'])
        end_time = calculate_end_time(session_data['selected_start_time'], total_time)
        end_time_after_break  = calculate_end_time_after_break(end_time)
        
        return {
            'end_time': end_time,
            'total_time': total_time,
            'selected_date': session_data['selected_date'],
            'selected_start_time': session_data['selected_start_time'],
            'end_time_after_break': end_time_after_break,
            'selected_services': get_service_names(session_data['selected_services_ids']),
            'total_price': calculate_total_price(session_data['selected_services_ids']),
        }

    
    def get(self, request):
        return self.render_page(request)
    
    def post(self, request):
        params = self.all_need_params_in_session(request)

        appointment, created = Appointment.objects.get_or_create(
            client=Client.objects.get(user=self.request.user),
            date=params['selected_date'],
            start_time=params['selected_start_time'],
            end_time=params['end_time'],
            end_time_after_break=params['end_time_after_break'],
            total_price = params['total_price'],
            total_time = params['total_time'],
            status='not_complete'
        )

        if created:
            for name in params['selected_services']:
                service = Service.objects.get(name=name)
                appointment.services.add(service)

            appointment.save

        return redirect('profile_user')
        


    
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



@login_required
def upload_picture(request):
    if request.method == "POST" and request.FILES.get("picture_user"):
        request.user.picture_user = request.FILES["picture_user"]
        request.user.save()
    return redirect("profile_user")























