# Generated by Django 2.0.5 on 2018-09-15 00:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0031_voteset_position'),
    ]

    operations = [
        migrations.AddField(
            model_name='position',
            name='new',
            field=models.CharField(max_length=1, null=True),
        ),
    ]
