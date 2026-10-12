import django
from django.db import migrations, models



class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MealPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('daily_calorie', models.IntegerField(verbose_name='Добова норма калорій (ккал)')),
                ('proteins', models.IntegerField(verbose_name='Білки (г)')),
                ('fats', models.IntegerField(verbose_name='Жири (г)')),
                ('carbs', models.IntegerField(verbose_name='Вуглеводи (г)')),
                ('users', models.ForeignKey(db_column='users_id', on_delete=django.db.models.deletion.CASCADE, related_name='meal_plans', to='accounts.fitnessuser')),
            ],
            options={
                'verbose_name': 'План харчування',
                'verbose_name_plural': 'Плани харчування',
                'db_table': 'meal_plans',
            },
        ),
        migrations.CreateModel(
            name='Workout',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=45, verbose_name='Назва тренування')),
                ('difficulty', models.CharField(max_length=45, verbose_name='Складність')),
                ('duration_min', models.IntegerField(verbose_name='Тривалість (хв)')),
                ('url', models.CharField(max_length=250, verbose_name='Посилання на вправу/відео')),
                ('users', models.ForeignKey(db_column='users_id', on_delete=django.db.models.deletion.CASCADE, related_name='workouts', to='accounts.fitnessuser')),
            ],
            options={
                'verbose_name': 'Тренування',
                'verbose_name_plural': 'Тренування',
                'db_table': 'workouts',
            },
        ),
    ]
