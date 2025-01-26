from django.core.mail import send_mail
from datetime import timedelta, datetime, date, time
from Beauty_Dom.settings import START_WORK, END_WORK, WORKDAY_DURATION, today, BREAK_AFTER_WORK
from .models import Service


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
    from .models import Appointment, NotAvailaibleDates
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
        if future_date not in occupied_slots:
            available_dates.append(future_date)
            continue

        # Проверяем, можно ли записаться в свободный временной интервал
        is_available = True
        future_start_time = datetime.combine(future_date, START_WORK)
        future_end_time = future_start_time + total_time

        for start_time, end_time in occupied_slots[future_date]:
            start_datetime = datetime.combine(future_date, start_time)
            end_datetime = datetime.combine(future_date, end_time)

            if future_end_time > start_datetime and future_start_time < end_datetime:
                is_available = False
                break

        if is_available:
        
            available_dates.append(future_date)

    # Проверим, какие даты из доступных являются недоступными
    common_dates = [date for date in available_dates if date not in not_available_dates]
        
    return common_dates

def calculate_total_time(service_ids):
    """Рассчитывает общее время для выбранных услуг."""
    selected_services = Service.objects.filter(id__in=service_ids)
    total_time = sum((service.time for service in selected_services), timedelta())
    return total_time

def calculate_total_price(service_ids):
    selected_services = Service.objects.filter(id__in=service_ids)
    total_price = sum(service.price for service in selected_services)
    return total_price

def calculate_end_time(selected_start_time, total_time):
    selected_start_time = datetime.strptime(selected_start_time, "%H:%M").time()
    datetime_obj = datetime.combine(datetime.today(), selected_start_time)
    end_time = datetime_obj + total_time
    return end_time.time()

def get_service_names(service_ids): 
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

    


