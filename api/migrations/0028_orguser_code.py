# Generated by Django 3.1.1 on 2020-11-01 16:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0027_auto_20201031_1208'),
    ]

    operations = [
        migrations.AddField(
            model_name='orguser',
            name='code',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
