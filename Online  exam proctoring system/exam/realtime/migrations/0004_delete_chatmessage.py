# Generated by Django 5.2.1 on 2025-07-09 20:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('realtime', '0003_remove_chatmessage_exam'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ChatMessage',
        ),
    ]
