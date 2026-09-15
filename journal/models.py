from django.db import models
from accounts.models import FitnessUser

class AiLog(models.Model):
    users = models.ForeignKey(FitnessUser, on_delete=models.CASCADE, related_name='ai_logs', db_column='users_id')
    request_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата запиту")
    recommendation_summary = models.CharField(max_length=1000, verbose_name="Підсумок рекомендації AI")
    workouts = models.ManyToManyField(
        'catalog.Workout', through='AiLogWorkout', related_name='ai_logs', blank=True,
        verbose_name="Тренування",
    )
    meal_plans = models.ManyToManyField(
        'catalog.MealPlan', through='AiLogMealPlan', related_name='ai_logs', blank=True,
        verbose_name="Плани харчування",
    )

    class Meta:
        db_table = 'ai_logs'
        verbose_name = "AI Лог"
        verbose_name_plural = "AI Логи"

    def __str__(self):
        return f"Лог #{self.id} для {self.users.username}"


class AiLogWorkout(models.Model):
    ai_logs = models.ForeignKey(
        AiLog, on_delete=models.CASCADE, related_name='ai_log_workouts', db_column='ai_logs_id',
    )
    workouts = models.ForeignKey(
        'catalog.Workout', on_delete=models.CASCADE, related_name='ai_log_workouts', db_column='workouts_id',
    )

    class Meta:
        db_table = 'ai_log_workouts'
        unique_together = [('ai_logs', 'workouts')]
        verbose_name = "Тренування в AI-логу"
        verbose_name_plural = "Тренування в AI-логах"


class AiLogMealPlan(models.Model):
    ai_logs = models.ForeignKey(
        AiLog, on_delete=models.CASCADE, related_name='ai_log_meal_plans', db_column='ai_logs_id',
    )
    meal_plans = models.ForeignKey(
        'catalog.MealPlan', on_delete=models.CASCADE, related_name='ai_log_meal_plans', db_column='meal_plans_id',
    )

    class Meta:
        db_table = 'ai_log_meal_plans'
        unique_together = [('ai_logs', 'meal_plans')]
        verbose_name = "План харчування в AI-логу"
        verbose_name_plural = "Плани харчування в AI-логах"
