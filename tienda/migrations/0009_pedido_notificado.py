# Generated by Django 4.2.16 on 2024-12-09 02:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tienda', '0008_venta'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedido',
            name='notificado',
            field=models.BooleanField(default=False),
        ),
    ]
