# Generated by Django 5.1.4 on 2025-01-15 08:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_catagory'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='catagory_name',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='store.catagory'),
            preserve_default=False,
        ),
    ]
