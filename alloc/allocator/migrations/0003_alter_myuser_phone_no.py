# Generated by Django 5.0.3 on 2024-09-05 04:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('allocator', '0002_remove_myuser_recovery_email_id_myuser_edu_email_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myuser',
            name='phone_no',
            field=models.CharField(max_length=15, unique=True),
        ),
    ]