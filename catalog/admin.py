from django.contrib import admin
from .models import MealPlan, Workout, UserWorkout

@admin.register(MealPlan)
class MealPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'users', 'daily_calorie', 'proteins', 'fats', 'carbs')

@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'users', 'title', 'difficulty', 'duration_min')

@admin.register(UserWorkout)
class UserWorkoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'users', 'workouts', 'assigned_date')
    list_filter = ('assigned_date',)
