from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_usermeasurement'),
    ]

    operations = [
        migrations.AddField(
            model_name='fitnessuser',
            name='health_restrictions',
            field=models.TextField(blank=True, null=True, verbose_name="Обмеження по здоров'ю / травми"),
        ),
    ]
