from django.db import migrations, models
from django.contrib.auth.hashers import make_password


def fill_auth_fields(apps, schema_editor):
    FitnessUser = apps.get_model('accounts', 'FitnessUser')
    hashed = make_password('TempPass1')
    for i, user in enumerate(FitnessUser.objects.all(), start=1):
        if not getattr(user, 'email', ''):
            user.email = f'user{i}@local.test'
        if not getattr(user, 'password', ''):
            user.password = hashed
        user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_fitnessuser_focus_muscle_group_fitnessuser_gender_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='fitnessuser',
            name='email',
            field=models.EmailField(default='legacy@local.test', max_length=254, verbose_name='Email'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='fitnessuser',
            name='password',
            field=models.CharField(default='', max_length=128, verbose_name='Пароль'),
            preserve_default=False,
        ),
        migrations.RunPython(fill_auth_fields, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='fitnessuser',
            name='email',
            field=models.EmailField(max_length=254, unique=True, verbose_name='Email'),
        ),
        migrations.AlterField(
            model_name='fitnessuser',
            name='username',
            field=models.CharField(max_length=45, unique=True, verbose_name="Ім'я користувача"),
        ),
        migrations.AlterField(
            model_name='fitnessuser',
            name='focus_muscle_group',
            field=models.CharField(
                choices=[
                    ('фулбаді', 'Фулбаді (по 1 вправі на групу)'),
                    ('груди', 'Груди'),
                    ('спина', 'Спина'),
                    ('ноги', 'Ноги'),
                    ('руки', 'Руки (біцепс, тріцепс, плечі)'),
                ],
                default='фулбаді',
                max_length=20,
                verbose_name="Пріоритетна група м'язів",
            ),
        ),
    ]
