# Generated by Django 5.1.6 on 2025-03-17 17:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0003_paymentorderitem_return_requested'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentorderitem',
            name='reason',
            field=models.TextField(blank=True, null=True),
        ),
    ]
