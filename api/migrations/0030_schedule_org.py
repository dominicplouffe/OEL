# Generated by Django 3.1.1 on 2020-11-01 20:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0029_auto_20201101_2045'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedule',
            name='org',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.org'),
        ),
    ]
