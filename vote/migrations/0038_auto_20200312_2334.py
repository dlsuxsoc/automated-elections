# Generated by Django 3.0.3 on 2020-03-12 23:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0037_position_priority'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='position',
            options={'ordering': ['priority']},
        ),
    ]
