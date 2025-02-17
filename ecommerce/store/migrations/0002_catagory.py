# Generated by Django 5.1.4 on 2025-01-15 08:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Catagory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('catagory_name', models.CharField(max_length=150)),
                ('cat_image', models.ImageField(blank=True, null=True, upload_to='')),
                ('Description', models.TextField(max_length=500)),
                ('status', models.BooleanField(default=False, help_text='0-Show,1-Hidden')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
