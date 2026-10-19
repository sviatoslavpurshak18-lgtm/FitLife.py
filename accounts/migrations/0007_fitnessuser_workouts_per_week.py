from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_fitnessuser_health_restrictions'),
    ]

    operations = [
        migrations.AddField(
            model_name='fitnessuser',
            name='workouts_per_week',
            field=models.IntegerField(default=3, verbose_name='Кількість тренувань на тиждень'),
        ),
    ]
