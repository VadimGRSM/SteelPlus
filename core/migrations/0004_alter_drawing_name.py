# Generated by Django 5.2.2 on 2025-06-20 07:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_remove_drawing_slug"),
    ]

    operations = [
        migrations.AlterField(
            model_name="drawing",
            name="name",
            field=models.CharField(max_length=255),
        ),
    ]
