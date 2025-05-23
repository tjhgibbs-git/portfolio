# Generated by Django 5.1.7 on 2025-03-12 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.TextField()),
                ('short_description', models.TextField()),
                ('image', models.ImageField(upload_to='projects/')),
                ('technologies', models.CharField(help_text='Comma-separated list of technologies', max_length=255)),
                ('url', models.URLField(blank=True)),
                ('github_url', models.URLField(blank=True)),
                ('date_created', models.DateField()),
                ('featured', models.BooleanField(default=False)),
            ],
        ),
    ]
