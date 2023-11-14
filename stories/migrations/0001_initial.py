# Generated by Django 3.2.9 on 2023-11-11 10:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Story',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=256)),
                ('description', models.TextField()),
                ('cover_prompt', models.CharField(max_length=1024)),
                ('solution', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Agent',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=256)),
                ('prompt', models.TextField()),
                ('story', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stories.story')),
            ],
        ),
    ]