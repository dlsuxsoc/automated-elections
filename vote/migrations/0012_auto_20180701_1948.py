# Generated by Django 2.0.5 on 2018-07-01 11:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0011_auto_20180701_1947'),
    ]

    operations = [
        migrations.AlterField(
            model_name='party',
            name='name',
            field=models.CharField(blank=True, max_length=32, null=True, unique=True),
        ),
    ]