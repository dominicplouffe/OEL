# Generated by Django 3.1.3 on 2021-01-08 12:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0055_pingheader_alert'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pingheader',
            name='ping',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.ping'),
        ),
    ]
