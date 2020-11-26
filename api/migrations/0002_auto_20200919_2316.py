# Generated by Django 3.1.1 on 2020-09-19 23:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ping',
            name='callback_url',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='ping',
            name='expected_string',
            field=models.CharField(blank=True, default='', max_length=1000),
            preserve_default=False,
        ),
    ]
