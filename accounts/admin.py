from django.contrib import admin
from .models import FitnessUser, UserMeasurement

@admin.register(FitnessUser)
class FitnessUserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'username', 'email', 'gender', 'date_of_birth', 'weight', 'height',
        'fitness_goal', 'focus_muscle_group', 'session_hours', 'bmi',
    )
    search_fields = ('username', 'email', 'fitness_goal')


@admin.register(UserMeasurement)
class UserMeasurementAdmin(admin.ModelAdmin):
    list_display = ('id', 'users', 'weight', 'height', 'recorded_at')
    list_filter = ('recorded_at',)
