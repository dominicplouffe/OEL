# Generated by Django 3.1.3 on 2021-01-22 00:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0066_auto_20210121_1609'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='failure',
            name='ping',
        ),
        migrations.RemoveField(
            model_name='pingheader',
            name='ping',
        ),
        migrations.RemoveField(
            model_name='result',
            name='ping',
        ),
    ]