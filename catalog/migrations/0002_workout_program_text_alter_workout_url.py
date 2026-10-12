import django
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='workout',
            name='program_text',
            field=models.TextField(blank=True, default='', verbose_name='Програма тренувань'),
        ),
        migrations.AlterField(
            model_name='workout',
            name='url',
            field=models.CharField(blank=True, max_length=250, verbose_name='Посилання на вправу/відео'),
        ),
    ]
