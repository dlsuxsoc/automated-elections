# Generated by Django 2.0.5 on 2018-07-01 06:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0006_auto_20180622_2259'),
    ]

    operations = [
        migrations.CreateModel(
            name='Party',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='candidate',
            name='party',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='vote.Party'),
            preserve_default=False,
        ),
    ]
