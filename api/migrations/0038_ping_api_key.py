# Generated by Django 3.1.3 on 2020-12-09 12:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0037_ping_direction'),
    ]

    operations = [
        migrations.AddField(
            model_name='ping',
            name='api_key',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]