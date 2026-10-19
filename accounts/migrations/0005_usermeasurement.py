import django.db.models.deletion
from django.db import migrations, models


def backfill_measurements(apps, schema_editor):
    FitnessUser = apps.get_model('accounts', 'FitnessUser')
    UserMeasurement = apps.get_model('accounts', 'UserMeasurement')
    for user in FitnessUser.objects.all():
        UserMeasurement.objects.create(users=user, weight=user.weight, height=user.height)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_remove_fullbody_focus'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserMeasurement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight', models.FloatField(verbose_name='Вага (кг)')),
                ('height', models.IntegerField(verbose_name='Зріст (см)')),
                ('recorded_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата запису')),
                ('users', models.ForeignKey(db_column='users_id', on_delete=django.db.models.deletion.CASCADE, related_name='measurements', to='accounts.fitnessuser')),
            ],
            options={
                'verbose_name': 'Замір користувача',
                'verbose_name_plural': 'Заміри користувачів',
                'db_table': 'user_measurements',
                'ordering': ['-recorded_at', '-id'],
            },
        ),
        migrations.RunPython(backfill_measurements, migrations.RunPython.noop),
    ]
