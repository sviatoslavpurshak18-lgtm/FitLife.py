import re
from django import forms
from .models import FitnessUser


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


class FitnessUserForm(forms.ModelForm):
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


class RegisterForm(forms.ModelForm):
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
