# Generated by Django 5.1.3 on 2025-01-26 17:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0021_alter_client_last_name_alter_client_name'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='videofile',
            options={'verbose_name': 'Видео', 'verbose_name_plural': 'Видео'},
        ),
        migrations.AlterField(
            model_name='client',
            name='phone_number',
            field=models.CharField(blank=True, max_length=11, null=True),
        ),
        migrations.AlterField(
            model_name='service',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='services/'),
        ),
        migrations.AlterField(
            model_name='videofile',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='videos', verbose_name='Файл с видео'),
        ),
    ]
