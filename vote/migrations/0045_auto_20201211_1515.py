# Generated by Django 3.1.2 on 2020-12-11 15:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0044_auto_20201128_1657'),
    ]

    operations = [
        migrations.AlterField(
            model_name='poll',
            name='name',
            field=models.CharField(max_length=250, unique=True),
        ),
    ]
