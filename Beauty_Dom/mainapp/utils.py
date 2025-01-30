from django.core.mail import send_mail
from datetime import timedelta, datetime, date, time
from Beauty_Dom.settings import START_WORK, END_WORK, WORKDAY_DURATION, today, BREAK_AFTER_WORK, STEP
from collections import defaultdict, namedtuple


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



def get_available_dates(selected_services):
    from .models import Appointment, NotAvailaibleDates, Service
    selected_services = Service.objects.filter(id__in=selected_services)
    not_available_dates = [obj.date for obj in list(NotAvailaibleDates.objects.all())]
    
    # Суммируем время всех выбранных услуг
    total_time = timedelta()
    for service in selected_services:
        total_time += service.time

    # Если общее время превышает рабочий день, возвращаем пустой список доступных дат
    if total_time > WORKDAY_DURATION:
        return []

    # Получаем текущую дату
    today = date.today()

    # Создаём список дат на 30 дней вперёд
    future_dates = [
        today + timedelta(days=i)
        for i in range(1, 31)
        if (today + timedelta(days=i)).weekday() < 5
    ]

    # Получаем записи с статусом 'not_complete' из базы данных
    not_complete_appointments = Appointment.objects.filter(status='not_complete')

    # Словарь для хранения занятых временных интервалов
    occupied_slots = {}

    # Заполняем занятые временные интервалы
    for appointment in not_complete_appointments:
        appointment_date = appointment.date
        if appointment_date not in occupied_slots:
            occupied_slots[appointment_date] = []
        # Добавляем интервал в занятые слоты (начало и конец записи)
        occupied_slots[appointment_date].append(
            (appointment.start_time, appointment.end_time)
        )

    # Список доступных дат
    available_dates = []

    # Формируем доступные даты с учетом занятых временных слотов
    for future_date in future_dates:
        if future_date in not_available_dates:
            continue  # Пропускаем заблокированные даты

        future_start_time = datetime.combine(future_date, START_WORK)
        future_end_time = future_start_time + total_time

        while future_end_time <= datetime.combine(future_date, END_WORK):
            is_available = True

            for start_time, end_time in occupied_slots.get(future_date, []):
                start_datetime = datetime.combine(future_date, start_time)
                end_datetime = datetime.combine(future_date, end_time)

                if future_end_time > start_datetime and future_start_time < end_datetime:
                    is_available = False
                    break

            if is_available:
                available_dates.append(future_date)
                break  # Если нашли свободное окно, день доступен

            future_start_time += timedelta(minutes=15)  # Двигаем время начала на 15 минут
            future_end_time = future_start_time + total_time  # Обновляем время окончания

    # Проверим, какие даты из доступных являются недоступными
    common_dates = [date for date in available_dates if date not in not_available_dates]
        
    return [date.isoformat() for date in common_dates]

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



def generate_time_slots(start_time, end_time, total_time=None):
    # Преобразуем start_time и end_time в datetime
    start = datetime.combine(datetime.today(), start_time)
    if total_time:
        end = datetime.combine(datetime.today(), end_time) - total_time
    else:
        end = datetime.combine(datetime.today(), end_time)
    
    time_slots = []
    
    current_time = start
    while current_time <= end:
        # Добавляем только время в список
        time_slots.append(current_time.time().strftime('%H:%M'))
        current_time += timedelta(minutes=15)
    
    return time_slots

def get_available_start_time(selected_date, total_time):
    from .models import Appointment
    time_list = generate_time_slots(START_WORK, END_WORK, total_time) 
    print(time_list)

    all_appointment_in_selected_date = Appointment.objects.filter(date=selected_date)
    print(all_appointment_in_selected_date)

    if not all_appointment_in_selected_date:
        return time_list
    
    # Список занятых временных интервалов
    occupied_slots = []
    selected_date_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
    for appointment in all_appointment_in_selected_date:
        start_time = appointment.start_time  # Время начала записи
        end_time = appointment.end_time  # Время окончания записи

        # Преобразуем время начала и окончания в datetime
        start_datetime = datetime.combine(selected_date_date_obj, start_time)
        end_datetime = datetime.combine(selected_date_date_obj, end_time)

        occupied_slots.append((start_datetime, end_datetime))

    not_available_dates = []

    # Проходим по каждому занятым интервалам и исключаем занятые слоты из доступных
    for start, end in datetime_list_to_str_list(occupied_slots):
        # Преобразуем строки времени обратно в объекты времени
        start_time = datetime.strptime(start, "%Y-%m-%d %H:%M").time()
        end_time = datetime.strptime(end, "%Y-%m-%d %H:%M").time()
        # Генерация временных интервалов для текущего занятый интервала
        slots = generate_time_slots(start_time, end_time)

        not_available_dates.extend(slots)

    return [item for item in time_list if item not in not_available_dates] 



    


class BaseClassTime:
    def _add_time(self, t: time, delta: timedelta) -> time:
        """Складывает time и timedelta без обработки перехода через полночь."""
        return (datetime(1, 1, 1, t.hour, t.minute, t.second) + delta).time()
    
    def _diff_time(self, delta: timedelta, t=END_WORK) -> time:
        return (datetime(1, 1, 1, t.hour, t.minute, t.second) - delta).time()
        
    def _subtract_time_slots(self, large_list, small_list):
        """Удаляет элементы из большого списка, которые есть в меньшем."""
        return [slot for slot in large_list if slot not in small_list]

    def _create_time_slots(self, time_duration=None, start_work=START_WORK, end_work=END_WORK, step=STEP):
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


    def _get_interval_slots(self, step=STEP):
        """Возвращает список временных слотов, используя параметры объекта (start_time, end_time) и метод из базового класса."""
        return self._create_time_slots(start_work=self.start_time, end_work=self.end_time, step=step,)
    

class Day(BaseClassTime):
    def __init__(self, date: date, time_duration: timedelta):
        self.date = date
        self.buzi_intervals = self._set_time_intervals()
        self.start_slots = self.get_start_time_list(time_duration)

    def _set_time_intervals(self):
        """Получаем интервалы на основе данных из модели Appointment для данной даты."""
        from .models import Appointment
        appointments = Appointment.objects.filter(date=self.date, status='not_complete')
        interval_list = []

        for appointment in appointments:
            interval_list.append(Interval(appointment.start_time, appointment.end_time_after_break))

        return interval_list

    def return_free_time_slots(self):
        """Удаляет элементы из большого списка, которые есть в одном или нескольких малых списках."""
        all_day_time_slots = self._create_time_slots()  # Вызываем метод из BaseClassTime напрямую

        time_slots = []
        for interval in self.intervals:
            time_slots.extend(interval._get_interval_slots())


        return self._subtract_time_slots(all_day_time_slots, time_slots)
    
    def get_start_time_list(self, time_duration: timedelta):
        all_day_time_slots_diff_dur = self._create_time_slots(time_duration=time_duration)
        
        free_time_slots = self.return_free_time_slots(all_day_time_slots_diff_dur)
        free_time_slots_add_dur = []
        
        for slot in free_time_slots:
            free_time_slots_add_dur.append(self._add_time(slot, time_duration))

        time_slots = []
        for interval in self.buzi_intervals:
            time_slots.extend(interval._get_interval_slots())

        result = [self._diff_time(time_duration, slot) for slot in self._subtract_time_slots(free_time_slots_add_dur, time_slots)]
        if not result:
            return 'not_available_times'
        return result

    @classmethod
    def create_some_days(cls, count, time_duration: timedelta):
        """Создает n дней начиная с завтрашнего дня."""
        current_date = datetime.now().date() + timedelta(days=1)  # Завтрашняя дата
        days = []

        for i in range(count):
            new_date = current_date + timedelta(days=i)
            days.append(cls(new_date, time_duration))  # Создание нового объекта Day для каждого дня

        return days
