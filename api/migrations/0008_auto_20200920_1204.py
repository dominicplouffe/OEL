# Generated by Django 3.1.1 on 2020-09-20 12:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_auto_20200920_0051'),
    ]

    operations = [
        migrations.AddField(
            model_name='ping',
            name='callback_num_calls',
            field=models.IntegerField(default=5),
        ),
        migrations.AddField(
            model_name='ping',
            name='failure_count',
            field=models.IntegerField(default=0),
        ),
    ]
