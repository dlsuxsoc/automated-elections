# Generated by Django 2.0.5 on 2018-09-15 00:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0030_remove_voter_currently_voting'),
    ]

    operations = [
        migrations.AddField(
            model_name='voteset',
            name='position',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='vote.Position'),
        ),
    ]
