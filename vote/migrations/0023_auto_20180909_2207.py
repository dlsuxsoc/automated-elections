# Generated by Django 2.0.5 on 2018-09-09 14:07

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0022_electionstatus'),
    ]

    operations = [
        migrations.CreateModel(
            name='VoteSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.RemoveField(
            model_name='vote',
            name='candidate',
        ),
        migrations.AddField(
            model_name='candidate',
            name='identifier',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=False),
        ),
        migrations.AddField(
            model_name='vote',
            name='serial_number',
            field=models.CharField(default=models.CharField(max_length=8, unique=True), max_length=6, unique=True),
        ),
        migrations.AddField(
            model_name='vote',
            name='voter_college',
            field=models.CharField(default='', max_length=3),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='take',
            name='response',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='vote',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterUniqueTogether(
            name='position',
            unique_together={('name', 'unit')},
        ),
        migrations.AddField(
            model_name='voteset',
            name='candidate',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vote.Candidate'),
        ),
        migrations.AddField(
            model_name='voteset',
            name='vote',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vote.Vote'),
        ),
    ]