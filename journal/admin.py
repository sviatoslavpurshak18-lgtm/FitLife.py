from django.contrib import admin
from .models import AiLog, AiLogWorkout, AiLogMealPlan

@admin.register(AiLog)
class AiLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'users', 'request_date', 'recommendation_summary')
    list_filter = ('request_date',)


@admin.register(AiLogWorkout)
class AiLogWorkoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'ai_logs', 'workouts')


@admin.register(AiLogMealPlan)
class AiLogMealPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'ai_logs', 'meal_plans')
