from django.shortcuts import render, redirect
from django.views.generic import FormView
from django.http import HttpResponse
from mainapp.models import *
from mainapp.forms import *
from mainapp.utils import *
from Beauty_Dom.settings import START_WORK, END_WORK, BREAK_AFTER_WORK, WORKDAY_DURATION





# представления для записи / несколько шагов

class AppointmentViewStep1(FormView):
    template_name = 'adminapp/appointment1.html'
    
    def get(self, request):


    def post(self, request):



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

    def get_data(self, request):
        return (self.request.session.get('selected_date'), 
            self.request.session.get('selected_services_ids'),
            self.request.session.get('selected_start_time')       
        )
    
    def get(self, request):
        selected_date, selected_services_ids, selected_start_time = self.get_data(request)

        return render(request, self.template_name, {
            'selected_start_time': selected_start_time,
            'selected_services': get_service_names(selected_services_ids),
            'selected_date': selected_date,
            'total_time': calculate_total_time(selected_services_ids), 
            'total_price': calculate_total_price(selected_services_ids),
            'end_time': calculate_end_time(selected_start_time, calculate_total_time(selected_services_ids))
        })
    
    def post(self, request):
        selected_date, selected_services_ids, selected_start_time = self.get_data(request)

        appointment = Appointment.objects.create(
            user=self.request.user,
            date=selected_date,
            start_time=datetime.strptime(selected_start_time, "%H:%M").time(),
            status='not_complete'
        )
        appointment.save
        return HttpResponse('готово')









