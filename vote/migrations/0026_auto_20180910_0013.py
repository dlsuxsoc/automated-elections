# Generated by Django 2.0.5 on 2018-09-09 16:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0025_auto_20180910_0008'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='position',
            unique_together={('base_position', 'unit')},
        ),
        migrations.RemoveField(
            model_name='position',
            name='name',
        ),
    ]