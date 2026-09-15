import datetime
from django.db import models
from accounts.models import FitnessUser

class MealPlan(models.Model):
    users = models.ForeignKey(FitnessUser, on_delete=models.CASCADE, related_name='meal_plans', db_column='users_id')
    daily_calorie = models.IntegerField(verbose_name="Добова норма калорій (ккал)")
    proteins = models.IntegerField(verbose_name="Білки (г)")
    fats = models.IntegerField(verbose_name="Жири (г)")
    carbs = models.IntegerField(verbose_name="Вуглеводи (г)")

    class Meta:
        db_table = 'meal_plans'
        verbose_name = "План харчування"
        verbose_name_plural = "Плани харчування"

    def __str__(self):
        return f"План {self.daily_calorie} ккал для {self.users.username}"


class Workout(models.Model):
    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    ]

    users = models.ForeignKey(FitnessUser, on_delete=models.CASCADE, related_name='workouts', db_column='users_id')
    title = models.CharField(max_length=45, verbose_name="Назва тренування")
    difficulty = models.CharField(max_length=45, choices=DIFFICULTY_CHOICES, verbose_name="Складність")
    duration_min = models.IntegerField(verbose_name="Тривалість (хв)")
    url = models.CharField(max_length=250, verbose_name="Посилання на вправу/відео", blank=True)
    program_text = models.TextField(blank=True, default='', verbose_name="Програма тренувань")
    assigned_users = models.ManyToManyField(
        FitnessUser, through='UserWorkout', related_name='assigned_workouts',
        verbose_name="Користувачі, яким призначено",
    )

    class Meta:
        db_table = 'workouts'
        verbose_name = "Тренування"
        verbose_name_plural = "Тренування"

    def __str__(self):
        return f"{self.title} ({self.difficulty}, {self.duration_min} хв)"


class UserWorkout(models.Model):
    users = models.ForeignKey(
        FitnessUser, on_delete=models.CASCADE, related_name='user_workouts', db_column='users_id',
    )
    workouts = models.ForeignKey(
        Workout, on_delete=models.CASCADE, related_name='user_workouts', db_column='workouts_id',
    )
    assigned_date = models.DateField(default=datetime.date.today, verbose_name="Дата призначення")

    class Meta:
        db_table = 'user_workouts'
        verbose_name = "Призначене тренування"
        verbose_name_plural = "Призначені тренування"

    def __str__(self):
        return f"{self.users.username} → {self.workouts.title} ({self.assigned_date})"
