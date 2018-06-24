# Generated by Django 2.0.5 on 2018-06-22 13:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0003_auto_20180618_2227'),
    ]

    operations = [
        migrations.AlterField(
            model_name='college',
            name='name',
            field=models.CharField(max_length=16, unique=True),
        ),
        migrations.AlterField(
            model_name='issue',
            name='name',
            field=models.CharField(max_length=64, unique=True),
        ),
        migrations.AlterField(
            model_name='position',
            name='name',
            field=models.CharField(max_length=32),
        ),
        migrations.AlterField(
            model_name='unit',
            name='batch',
            field=models.CharField(max_length=4, null=True),
        ),
        migrations.AlterField(
            model_name='unit',
            name='name',
            field=models.CharField(max_length=16, unique=True),
        ),
        migrations.AlterField(
            model_name='vote',
            name='voter_id_number',
            field=models.CharField(max_length=8, unique=True),
        ),
    ]