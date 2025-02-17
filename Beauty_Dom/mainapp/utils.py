from django.core.mail import send_mail
from datetime import timedelta, datetime, date, time
from Beauty_Dom.settings import START_WORK, END_WORK, BREAK_AFTER_WORK, STEP
from rest_framework import serializers


def send_activation_code(email, verification_link):
    send_mail(
        'Подтверждение почты',
        f'Ваша ссылка активации: {verification_link} перейдите по ней чтобы активировать аккаунт',
        'beautydom42@gmail.com',
        [email],
        fail_silently=False,
    )

def send_recover_link(email, recover_password_link):
    send_mail(
        'Восстановление пароля',
        f'Ваша ссылка для восстановления пароля: {recover_password_link} \nЕсли вы не пытались востановить пароль проигнорируйе это сообщение',
        'beautydom42@gmail.com',
        [email],
        fail_silently=False
    )


def datetime_list_to_str_list(datetime_list, fmt="%Y-%m-%d %H:%M"):
    """
    Преобразует список объектов datetime в список строк.
    
    :param datetime_list: Список объектов datetime
    :param fmt: Формат строки (по умолчанию "%Y-%m-%d %H:%M")
    :return: Список строк
    """
    return [[dt_start.strftime(fmt), dt_end.strftime(fmt)] for dt_start, dt_end in datetime_list]


def str_list_to_datetime_list(str_list, fmt="%Y-%m-%d %H:%M"):
    """
    Преобразует список строк в список объектов datetime.
    
    :param str_list: Список строк
    :param fmt: Формат строки (по умолчанию "%Y-%m-%d %H:%M")
    :return: Список объектов datetime
    """
    return [[datetime.strptime(str_start, fmt), datetime.strptime(str_end, fmt)] for str_start, str_end  in str_list]


def calculate_total_time(service_ids):
    from .models import Service
    """Рассчитывает общее время для выбранных услуг."""
    selected_services = Service.objects.filter(id__in=service_ids)
    total_time = sum((service.time for service in selected_services), timedelta())
    return total_time

def calculate_total_price(service_ids):
    from .models import Service
    selected_services = Service.objects.filter(id__in=service_ids)
    total_price = sum(service.price for service in selected_services)
    return total_price

def calculate_end_time(selected_start_time: str, total_time: timedelta) -> datetime.time:
    # Преобразуем строку времени в объект datetime
    start_time_obj = datetime.strptime(selected_start_time, "%H:%M")
    
    # Добавляем продолжительность
    end_time = start_time_obj + total_time
    
    # Возвращаем результат в формате строки
    return end_time.time()

def calculate_end_time_after_break(end_time: datetime.time, break_after_work=BREAK_AFTER_WORK) -> datetime.time:
    end_time = datetime.combine(date.today(), end_time)
    end_time_after_work = break_after_work + end_time
    return end_time_after_work.time()


def get_service_names(service_ids):
    from .models import Service
    selected_services = Service.objects.filter(id__in=service_ids)
    names = [service.name for service in selected_services]
    return names





class BaseClassTime:
    def _add_time(self, t: time, delta: timedelta) -> time:
        """Складывает time и timedelta"""
        return (datetime(1, 1, 1, t.hour, t.minute, t.second) + delta).time()
    
    def _diff_time(self, delta: timedelta, t=END_WORK) -> time:
        return (datetime(1, 1, 1, t.hour, t.minute, t.second) - delta).time()
        
    def _subtract_time_slots(self, all_slots, busy_slots):
        """Удаляет элементы из большого списка, которые есть в меньшем."""
        return [slot for slot in all_slots if slot not in busy_slots]

    def _create_time_slots(self, time_duration=None, start_work=START_WORK, end_work=END_WORK, step=STEP) -> list:
        time_slots = []
        current_time = start_work

        if time_duration:
            end_work = self._diff_time(time_duration)
        

        while current_time <= end_work:
            time_slots.append(current_time)
            current_time = self._add_time(current_time, step)

        return time_slots
    

class Interval(BaseClassTime):
    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time
        self.end_time_after_break = self._set_time_after_break()
        self.time_slots = self._get_interval_slots()

    def _set_time_after_break(self, break_after_work=BREAK_AFTER_WORK):
        """Устанавливает время после перерыва"""
        return self._add_time(self.end_time, break_after_work)

    def _get_interval_slots(self, step=STEP) -> list:
        """Возвращает список временных слотов, используя параметры объекта (start_time, end_time) и метод из базового класса."""
        return self._create_time_slots(start_work=self.start_time, end_work=self.end_time_after_break, step=step)[:-1]



class Day(BaseClassTime):
    def __init__(self, date: date, time_duration: timedelta):
        self._date = date
        self._busy_intervals = self._set_time_intervals()
        self._busy_time_slots = self._set_busy_time_slots()
        self._start_slots = self._create_start_time_list(time_duration)
        self.is_available = self.get_start_time_list() is not None

    def _set_time_intervals(self):
        """Получаем интервалы на основе данных из модели Appointment для данной даты."""
        from .models import Appointment
        appointments = Appointment.objects.filter(date=self._date, status='not_complete')
        interval_list = []

        for appointment in appointments:
            interval_list.append(Interval(appointment.start_time, appointment.end_time))

        return interval_list

    def _set_busy_time_slots(self):
        busy_time_slots = []

        for interval in self._busy_intervals:
            busy_time_slots += interval.time_slots
        print(busy_time_slots)
        return busy_time_slots


    def _return_free_time_slots(self, all_day_time_slots=None):
        """Удаляет элементы из большого списка, которые есть в одном или нескольких малых списках."""
        if all_day_time_slots is None:
            all_day_time_slots = self._create_time_slots()

        time_slots = []
        for interval in self._busy_intervals:
            time_slots.extend(interval._get_interval_slots())


        return self._subtract_time_slots(all_day_time_slots, time_slots)

    
    def _create_start_time_list(self, time_duration: timedelta):
        """Возвращает список доступных для начала процедыр дат"""
        all_day_time_slots_diff_dur = self._create_time_slots(time_duration=time_duration)
        
        free_time_slots = self._return_free_time_slots(all_day_time_slots_diff_dur)
        free_time_slots_add_dur = [self._add_time(slot, time_duration) for slot in free_time_slots]

        time_slots = []
        for interval in self._busy_intervals:
            time_slots.extend(interval._get_interval_slots())

        result = [self._diff_time(time_duration, slot) for slot in self._subtract_time_slots(free_time_slots_add_dur, time_slots)]

        if not result:
            return None
        
        return result
    
    def checkout_intervals_croses(self, interval):
        time_slots = set(interval._get_interval_slots())

        if time_slots in self._busy_time_slots:
            return True 

        return False


    def get_date(self):
        return self._date
    
    def get_date_str(self):
        return self._date.strftime('%Y-%m-%d') 
    
    def get_start_time_list(self):
        return self._start_slots

    def get_start_time_list_str(self):
        return [slot.strftime('%H:%M') for slot in self._start_slots]

    

    @classmethod
    def create_some_days(cls, count, time_duration: timedelta):
        """Создает n дней начиная с завтрашнего дня."""
        current_date = datetime.now().date() + timedelta(days=1)  # Завтрашняя дата
        days = []
        forbiden_dates = cls._create_forbiden_list_days()

        while len(days) < count:
            if current_date not in forbiden_dates and current_date.weekday() not in [5, 6]:
                days.append(cls(current_date, time_duration))
            current_date += timedelta(days=1)
        return days
    
    @classmethod
    def _create_forbiden_list_days(cls):
        '''Создает список запрещеных дат для бронирования'''
        from .models import NotAvailaibleDates
        forbiden_dates = NotAvailaibleDates.objects.all()
        
        return [date.date for date in forbiden_dates]

    
    @classmethod 
    def create_available_list_days(cls, count, time_duration: timedelta) -> list:
        """Возвращает список и словарь вида 
        [date1, date2, date3] - нужно для 2 этапа формы
        {date1: [time_slot1, time_slot1], date2: [time_slot1, time_slot1]  } - нужно для 3 этапа формы
        для доступных дат на count дней вперед"""
        days_list = cls.create_some_days(count=count, time_duration=time_duration)

        available_dates_times = {}
        available_dates = []

        for day in days_list:
            if day.is_available:
                available_dates.append(day.get_date_str())
                available_dates_times[day.get_date_str()] = day.get_start_time_list_str()

        return available_dates, available_dates_times
    

class IntervalSerializator(serializers.Serializer):
    start_time = serializers.TimeField(format="%H:%M")
    end_time = serializers.TimeField(format="%H:%M")
    end_time_after_break = serializers.TimeField(format="%H:%M")

    def to_representation(self, instance):
        return {
            'start_time': str(instance.start_time),
            'end_time': str(instance.end_time),
            'end_time_after_break': str(instance.end_time_after_break)
        }

class DaySerialazable(serializers.Serializer):
    date = serializers.DateField(source='_date')
    busy_intervals = IntervalSerializator(source='_busy_intervals', many=True)  # Список объектов Interval
    busy_time_slots = serializers.ListField(source='_busy_time_slots', child=serializers.TimeField(format="%H:%M"))
    start_slots = serializers.ListField(child=serializers.TimeField(format="%H:%M"))
    is_available = serializers.BooleanField()


def make_appointment(request, params, selected_date):
    """Функция для создания записи проверяет нет ли уже такой записи 
    и проверяет не пересикается ли запись с кемто еще"""
    from .models import Appointment, Client, Service


    
    appointment, created = Appointment.objects.get_or_create(
        client=Client.objects.get(user=request.user),
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


# def get_available_dates(selected_date):


# def get_available_start_time(selected_date):
