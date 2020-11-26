# Generated by Django 3.1.1 on 2020-09-20 00:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_auto_20200920_0017'),
    ]

    operations = [
        migrations.AlterField(
            model_name='failure',
            name='reason',
            field=models.CharField(blank=True, choices=[('invalid_value', 'Invalid Value'), ('key_error', 'Key Error'), ('value_error', 'Value Error'), ('status_code', 'Status Code')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='result',
            name='total_time',
            field=models.FloatField(),
        ),
    ]
