import datetime
from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class FitnessUser(models.Model):
    GENDER_CHOICES = [
        ('чоловік', 'Чоловік'),
        ('жінка', 'Жінка'),
    ]
    FOCUS_CHOICES = [
        ('груди', 'Груди'),
        ('спина', 'Спина'),
        ('ноги', 'Ноги'),
        ('руки', 'Руки (біцепс, тріцепс, плечі)'),
    ]

    username = models.CharField(max_length=45, unique=True, verbose_name="Ім'я користувача")
    email = models.EmailField(unique=True, verbose_name="Email")
    password = models.CharField(max_length=128, verbose_name="Пароль")
    date_of_birth = models.IntegerField(verbose_name="Рік народження")
    weight = models.FloatField(verbose_name="Вага (кг)")
    height = models.IntegerField(verbose_name="Зріст (см)")
    fitness_goal = models.CharField(max_length=45, verbose_name="Ціль")
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default='чоловік', verbose_name="Стать")
    workouts_per_week = models.IntegerField(default=3, verbose_name="Кількість тренувань на тиждень")
    focus_muscle_group = models.CharField(
        max_length=20,
        choices=FOCUS_CHOICES,
        default='груди',
        verbose_name="Пріоритетна група м'язів",
    )
    session_hours = models.FloatField(default=2.0, verbose_name="Тривалість тренування (год)")
    health_restrictions = models.TextField(blank=True, null=True, verbose_name="Обмеження по здоров'ю / травми")

    class Meta:
        db_table = 'users'
        verbose_name = "Користувач"
        verbose_name_plural = "Користувачі"

    def __str__(self):
        return f"{self.username} ({self.fitness_goal})"

    @property
    def age(self):
        return datetime.date.today().year - self.date_of_birth if self.date_of_birth else 20

    @property
    def bmi(self):
        h_m = self.height / 100.0
        return round(self.weight / (h_m ** 2), 1) if h_m > 0 else 0.0

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.record_measurement()
        from . import json_store
        json_store.save_user(self)

    def record_measurement(self):
        """Додає запис у user_measurements, якщо вага або зріст змінились."""
        last = self.measurements.first()
        if last is None or last.weight != self.weight or last.height != self.height:
            UserMeasurement.objects.create(users=self, weight=self.weight, height=self.height)

    def delete(self, *args, **kwargs):
        user_id = self.pk
        result = super().delete(*args, **kwargs)
        from . import json_store
        json_store.delete_user(user_id)
        return result

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)


class UserMeasurement(models.Model):
    users = models.ForeignKey(
        FitnessUser, on_delete=models.CASCADE, related_name='measurements', db_column='users_id',
    )
    weight = models.FloatField(verbose_name="Вага (кг)")
    height = models.IntegerField(verbose_name="Зріст (см)")
    recorded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата запису")

    class Meta:
        db_table = 'user_measurements'
        ordering = ['-recorded_at', '-id']
        verbose_name = "Замір користувача"
        verbose_name_plural = "Заміри користувачів"

    def __str__(self):
        return f"{self.users.username}: {self.weight} кг, {self.height} см ({self.recorded_at:%d.%m.%Y})"
