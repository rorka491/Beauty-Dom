from django.shortcuts import render, redirect
from django.views.generic import FormView
from django.http import HttpResponse
from mainapp.models import *
from adminapp.forms import *
from mainapp.utils import *
from Beauty_Dom.settings import START_WORK, END_WORK, BREAK_AFTER_WORK, WORKDAY_DURATION
from django.contrib.auth.mixins import LoginRequiredMixin


# представления для записи / несколько шагов
class BaseAppointmentViewStep(FormView):
    def get_session_data(self, keys):
        if isinstance(keys, str):
            return self.request.session.get(keys)
        
        return {key: self.request.session.get(key) for key in keys}
    

    def save_session_data(self, data):
        for key, value in data.items():
            self.request.session[key] = value

# представления для записи / несколько шагов
class AdminAppointmentViewStep1(LoginRequiredMixin, BaseAppointmentViewStep):
    template_name = 'adminapp/appointment0.html'

    def get(self, request):
        form = ClientInfoform()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ClientInfoform(request.POST)
        if form.is_valid():
            phone_number = str(form.cleaned_data['phone_number'])
            name = str(form.cleaned_data['name'])
            last_name = str(form.cleaned_data['last_name'])

            self.request.session['phone_number'] = phone_number

            client, created = Client.objects.get_or_create(
            phone_number=phone_number,
            defaults={
                'name': name,
                'last_name': last_name,
            })       

            
            return redirect('form_step2')

        return render(request, self.template_name, {'form': form})



class AdminAppointmentViewStep2(LoginRequiredMixin, BaseAppointmentViewStep):
    template_name = 'mainapp/appointment1.html'

    def render_page(self, request, error_messages=None):
        services = Service.objects.all().order_by('service_type')
        step_text = 'Выберите услугу'
        step_count = 2


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

        return redirect('form_step3')



class AdminAppointmentViewStep3(LoginRequiredMixin, BaseAppointmentViewStep):
    template_name = 'adminapp/appointment2.html'

    form_class = DateForm

    def render_page(self, request, error_messages=None):
        available_dates = self.get_session_data('available_dates')
        form = self.form_class
        step_text = 'Выберите день'
        step_count = 3


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

            return redirect('form_step4')
        
        return self.render_page(request)



   
class AdminAppointmentViewStep4(LoginRequiredMixin, BaseAppointmentViewStep):
    template_name = 'adminapp/appointment3.html'
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
        step_count = 4
        return render(request, self.template_name, {'form': form,
                                                    'step_text': step_text,
                                                    'step_count': step_count})
    
    def get(self, request):
        return self.render_page(request)
    
    def post(self, request):
        form = self.form_class(request.POST, choices=self.get_choices())

        if form.is_valid():
            self.save_session_data({'selected_start_time': str(form.cleaned_data['start_time'])})
            return redirect('form_step5')

        return self.render_page(request, form)

    
class AdminAppointmentViewStep5(LoginRequiredMixin, BaseAppointmentViewStep):
    template_name = 'adminapp/appointment4.html'

    def render_page(self, request):
        params = self.all_need_params_in_session(request)
        params['step_text'] = 'Подтвердите запись'
        params['step_count'] = 5
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

        return redirect('form_step1')
    


