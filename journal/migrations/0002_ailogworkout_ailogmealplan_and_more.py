import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0003_userworkout_workout_assigned_users_and_more'),
        ('journal', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AiLogWorkout',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ai_logs', models.ForeignKey(db_column='ai_logs_id', on_delete=django.db.models.deletion.CASCADE, related_name='ai_log_workouts', to='journal.ailog')),
                ('workouts', models.ForeignKey(db_column='workouts_id', on_delete=django.db.models.deletion.CASCADE, related_name='ai_log_workouts', to='catalog.workout')),
            ],
            options={
                'verbose_name': 'Тренування в AI-логу',
                'verbose_name_plural': 'Тренування в AI-логах',
                'db_table': 'ai_log_workouts',
                'unique_together': {('ai_logs', 'workouts')},
            },
        ),
        migrations.CreateModel(
            name='AiLogMealPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ai_logs', models.ForeignKey(db_column='ai_logs_id', on_delete=django.db.models.deletion.CASCADE, related_name='ai_log_meal_plans', to='journal.ailog')),
                ('meal_plans', models.ForeignKey(db_column='meal_plans_id', on_delete=django.db.models.deletion.CASCADE, related_name='ai_log_meal_plans', to='catalog.mealplan')),
            ],
            options={
                'verbose_name': 'План харчування в AI-логу',
                'verbose_name_plural': 'Плани харчування в AI-логах',
                'db_table': 'ai_log_meal_plans',
                'unique_together': {('ai_logs', 'meal_plans')},
            },
        ),
        migrations.AddField(
            model_name='ailog',
            name='workouts',
            field=models.ManyToManyField(blank=True, related_name='ai_logs', through='journal.AiLogWorkout', to='catalog.workout', verbose_name='Тренування'),
        ),
        migrations.AddField(
            model_name='ailog',
            name='meal_plans',
            field=models.ManyToManyField(blank=True, related_name='ai_logs', through='journal.AiLogMealPlan', to='catalog.mealplan', verbose_name='Плани харчування'),
        ),
    ]
