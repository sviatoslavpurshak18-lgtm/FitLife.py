import datetime
import re
from django import forms
from .models import FitnessUser

# Обмеження для анкетних даних
MIN_AGE = 16          # у зал — з 16 років (у 2026 році це рік народження не пізніше 2010)
MAX_AGE = 100
MIN_WEIGHT = 30       # кг
MIN_HEIGHT = 100      # см


class BodyDataValidationMixin:
    """Перевірка року народження, ваги й зросту (спільна для реєстрації та редагування профілю)."""

    @staticmethod
    def _birth_year_limits():
        year = datetime.date.today().year
        return year - MAX_AGE, year - MIN_AGE

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        min_year, max_year = self._birth_year_limits()
        limits = {
            'date_of_birth': {'min': min_year, 'max': max_year, 'placeholder': f'Не пізніше {max_year}'},
            'weight': {'min': MIN_WEIGHT, 'placeholder': f'Від {MIN_WEIGHT} кг'},
            'height': {'min': MIN_HEIGHT, 'placeholder': f'Від {MIN_HEIGHT} см'},
        }
        for name, attrs in limits.items():
            if name in self.fields:
                self.fields[name].widget.attrs.update(attrs)

    def clean_date_of_birth(self):
        year = self.cleaned_data.get('date_of_birth')
        min_year, max_year = self._birth_year_limits()
        if year is not None:
            if year > max_year:
                raise forms.ValidationError(
                    f'Користуватись сервісом можна з {MIN_AGE} років: рік народження не пізніше {max_year}.'
                )
            if year < min_year:
                raise forms.ValidationError(f'Рік народження не може бути раніше {min_year}.')
        return year

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight is not None and weight < MIN_WEIGHT:
            raise forms.ValidationError(f'Вага має бути не менше {MIN_WEIGHT} кг.')
        return weight

    def clean_height(self):
        height = self.cleaned_data.get('height')
        if height is not None and height < MIN_HEIGHT:
            raise forms.ValidationError(f'Зріст має бути не менше {MIN_HEIGHT} см.')
        return height


COMMON_WIDGETS = {
    'username': forms.TextInput(attrs={'class': 'form-control'}),
    'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'you@email.com'}),
    'date_of_birth': forms.NumberInput(attrs={'class': 'form-control'}),
    'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
    'height': forms.NumberInput(attrs={'class': 'form-control'}),
    'fitness_goal': forms.Select(
        choices=[
            ('Набір маси', 'Набір маси'),
            ('Схуднення', 'Схуднення'),
            ('Підтримка форми', 'Підтримка форми'),
        ],
        attrs={'class': 'form-select'},
    ),
    'gender': forms.Select(attrs={'class': 'form-select'}),
    'workouts_per_week': forms.Select(
        choices=[
            (1, '1 раз на тиждень'),
            (2, '2 рази на тиждень'),
            (3, '3 рази на тиждень'),
        ],
        attrs={'class': 'form-select'},
    ),
    'focus_muscle_group': forms.Select(attrs={'class': 'form-select'}),
    'session_hours': forms.Select(
        choices=[
            (1.0, '1 година'),
            (1.5, '1.5 години'),
            (2.0, '2 години'),
            (2.5, '2.5 години'),
            (3.0, '3 години'),
        ],
        attrs={'class': 'form-select'},
    ),
    'health_restrictions': forms.Textarea(attrs={
        'class': 'form-control', 
        'rows': 2, 
        'placeholder': "Наприклад: протрузія попереку, біль у колінах (або залиште порожнім)"
    }),
}


class FitnessUserForm(BodyDataValidationMixin, forms.ModelForm):
    class Meta:
        model = FitnessUser
        fields = [
            'username',
            'email',
            'date_of_birth',
            'weight',
            'height',
            'fitness_goal',
            'gender',
            'workouts_per_week',
            'focus_muscle_group',
            'session_hours',
            'health_restrictions',
        ]
        widgets = COMMON_WIDGETS


class RegisterForm(BodyDataValidationMixin, forms.ModelForm):
    field_order = [
        'username',
        'email',
        'password',
        'password2',
        'date_of_birth',
        'weight',
        'height',
        'gender',
        'workouts_per_week',
        'fitness_goal',
        'focus_muscle_group',
        'session_hours',
        'health_restrictions',
    ]
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Мінімум 8 символів'}),
    )
    password2 = forms.CharField(
        label='Підтвердження пароля',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Повторіть пароль'}),
    )

    class Meta:
        model = FitnessUser
        fields = [
            'username',
            'email',
            'date_of_birth',
            'weight',
            'height',
            'gender',
            'workouts_per_week',
            'fitness_goal',
            'focus_muscle_group',
            'session_hours',
            'health_restrictions',
        ]
        widgets = COMMON_WIDGETS
        help_texts = {
            'workouts_per_week': 'Кількість днів тренувань на тиждень (від 1 до 3).',
            'focus_muscle_group': "На обрану групу м'язів — до 3 вправ за тренування, на решту груп — по 1 вправі.",
            'session_hours': 'Програма підганяється під цей час і не виходить за нього.',
        }

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise forms.ValidationError('Вкажіть email.')
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            raise forms.ValidationError('Некоректний формат email.')
        if FitnessUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Цей email вже зареєстровано.')
        return email

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if FitnessUser.objects.filter(username=username).exists():
            raise forms.ValidationError("Таке ім'я користувача вже зайняте.")
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password') or ''
        if len(password) < 8:
            raise forms.ValidationError('Пароль має містити щонайменше 8 символів.')
        if password.isdigit():
            raise forms.ValidationError('Пароль не може складатися лише з цифр.')
        if password.lower() == password:
            raise forms.ValidationError('Додайте хоча б одну велику літеру.')
        if not re.search(r'\d', password):
            raise forms.ValidationError('Додайте хоча б одну цифру.')
        return password

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        password2 = cleaned.get('password2')
        if password and password2 and password != password2:
            self.add_error('password2', 'Паролі не збігаються.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = user.email.lower()
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'you@email.com', 'autofocus': True}),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def clean(self):
        cleaned = super().clean()
        email = (cleaned.get('email') or '').strip().lower()
        password = cleaned.get('password') or ''
        user = FitnessUser.objects.filter(email__iexact=email).first()
        if not user or not user.check_password(password):
            raise forms.ValidationError('Невірний email або пароль.')
        self.fitness_user = user
        return cleaned