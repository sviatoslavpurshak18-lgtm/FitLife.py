import datetime

import django.db.models.deletion
from django.db import migrations, models


def backfill_user_workouts(apps, schema_editor):
    Workout = apps.get_model('catalog', 'Workout')
    UserWorkout = apps.get_model('catalog', 'UserWorkout')
    for workout in Workout.objects.all():
        UserWorkout.objects.create(users_id=workout.users_id, workouts=workout)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('catalog', '0002_workout_program_text_alter_workout_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserWorkout',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assigned_date', models.DateField(default=datetime.date.today, verbose_name='Дата призначення')),
                ('users', models.ForeignKey(db_column='users_id', on_delete=django.db.models.deletion.CASCADE, related_name='user_workouts', to='accounts.fitnessuser')),
                ('workouts', models.ForeignKey(db_column='workouts_id', on_delete=django.db.models.deletion.CASCADE, related_name='user_workouts', to='catalog.workout')),
            ],
            options={
                'verbose_name': 'Призначене тренування',
                'verbose_name_plural': 'Призначені тренування',
                'db_table': 'user_workouts',
            },
        ),
        migrations.AddField(
            model_name='workout',
            name='assigned_users',
            field=models.ManyToManyField(related_name='assigned_workouts', through='catalog.UserWorkout', to='accounts.fitnessuser', verbose_name='Користувачі, яким призначено'),
        ),
        migrations.AlterField(
            model_name='workout',
            name='difficulty',
            field=models.CharField(choices=[('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard')], max_length=45, verbose_name='Складність'),
        ),
        migrations.RunPython(backfill_user_workouts, migrations.RunPython.noop),
    ]
