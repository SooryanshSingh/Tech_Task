# Generated by Django 5.0.6 on 2024-06-14 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Home', '0013_exam_end_time_exam_start_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProctorEmail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
            ],
        ),
    ]
