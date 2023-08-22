# Generated by Django 4.2.4 on 2023-08-21 21:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("main_app", "0008_alter_childtransaction_transaction"),
    ]

    operations = [
        migrations.AlterField(
            model_name="childtransaction",
            name="transaction",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="childtransactions",
                to="main_app.transaction",
            ),
        ),
    ]
