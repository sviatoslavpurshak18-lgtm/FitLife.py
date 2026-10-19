from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FitnessUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=45, verbose_name="Ім'я користувача")),
                ('date_of_birth', models.IntegerField(verbose_name='Рік народження')),
                ('weight', models.FloatField(verbose_name='Вага (кг)')),
                ('height', models.IntegerField(verbose_name='Зріст (см)')),
                ('fitness_goal', models.CharField(max_length=45, verbose_name='Ціль')),
            ],
            options={
                'verbose_name': 'Користувач',
                'verbose_name_plural': 'Користувачі',
                'db_table': 'users',
            },
        ),
    ]
