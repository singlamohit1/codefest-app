# Generated by Django 2.1.5 on 2019-03-30 20:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Auth', '0002_auto_20190331_0158'),
    ]

    operations = [
        migrations.AlterField(
            model_name='verifiedaccount',
            name='provider_uid',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]