# Generated by Django 5.0.6 on 2024-05-30 10:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Home', '0004_response'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CustomUser',
        ),
    ]