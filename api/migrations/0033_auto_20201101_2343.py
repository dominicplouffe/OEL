# Generated by Django 3.1.1 on 2020-11-01 23:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0032_schedule_color'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='schedule',
            name='color',
        ),
        migrations.AddField(
            model_name='orguser',
            name='color',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
