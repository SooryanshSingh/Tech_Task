# Generated by Django 5.0.6 on 2024-06-07 10:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Home', '0009_alter_mark_marks'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mark',
            name='question',
        ),
    ]
