# Generated by Django 3.1.3 on 2020-12-09 21:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0042_auto_20201209_2117'),
    ]

    operations = [
        migrations.AddField(
            model_name='failure',
            name='recovered_on',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]