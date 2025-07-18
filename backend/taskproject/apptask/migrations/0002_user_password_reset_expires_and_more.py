# Generated by Django 5.2.4 on 2025-07-15 17:22

import apptask.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apptask', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='password_reset_expires',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='password_reset_token',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='dni',
            field=models.CharField(help_text='Cédula ecuatoriana de 10 dígitos', max_length=10, unique=True, validators=[apptask.models.validate_cedula_ecuatoriana]),
        ),
    ]
