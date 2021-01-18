# Generated by Django 3.1.3 on 2021-01-08 03:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0053_alert_org'),
    ]

    operations = [
        migrations.AlterField(
            model_name='failure',
            name='ping',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.ping'),
        ),
        migrations.AlterField(
            model_name='result',
            name='ping',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.ping'),
        ),
    ]
