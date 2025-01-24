from django import forms


# """Многоступенчатая форма"""

class ClientInfoform(forms.Form):
    name = forms.CharField(label='', max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Имя'}))
    last_name = forms.CharField(label='', max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Фамилия'}))
    phone_number = forms.CharField(label='', max_length=11, min_length=11, widget=forms.TextInput(attrs={'placeholder': 'Телефон'}))



class DateForm(forms.Form):
    date = forms.DateField(label='',
        widget=forms.DateInput(
            attrs={
                'type': 'text',
                'id': 'datepicker',
                'placeholder': 'Выберите дату'
            }
        )
    )

class StartTimeForm(forms.Form):
    start_time = forms.ChoiceField(
        label='', 
        choices=[],
        widget=forms.Select(
            attrs={
                'id': 'timepicker',
                'placeholder': 'Выберите время'
            }
        )
    )
    
    def __init__(self, *args, choices, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_time'].choices = choices

class NotesForm(forms.Form):
    notes = forms.CharField(label='', max_length=1000, widget=forms.TextInput(attrs={'placeholder': 'Запись '}))



