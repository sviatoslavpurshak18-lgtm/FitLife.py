from django.db import migrations, models


def fullbody_to_chest(apps, schema_editor):
    FitnessUser = apps.get_model('accounts', 'FitnessUser')
    FitnessUser.objects.filter(focus_muscle_group='фулбаді').update(focus_muscle_group='груди')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_fitnessuser_email_password'),
    ]

    operations = [
        migrations.RunPython(fullbody_to_chest, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='fitnessuser',
            name='focus_muscle_group',
            field=models.CharField(
                choices=[
                    ('груди', 'Груди'),
                    ('спина', 'Спина'),
                    ('ноги', 'Ноги'),
                    ('руки', 'Руки (біцепс, тріцепс, плечі)'),
                ],
                default='груди',
                max_length=20,
                verbose_name="Пріоритетна група м'язів",
            ),
        ),
    ]
