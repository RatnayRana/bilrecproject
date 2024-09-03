# Generated by Django 5.0.7 on 2024-09-03 05:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Bank",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="System",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("username", models.CharField(max_length=150)),
                ("employee_id", models.CharField(max_length=100)),
                ("email", models.CharField(max_length=100)),
                ("cid", models.IntegerField()),
                ("status", models.CharField(default="Inactive", max_length=50)),
                ("user_created", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="BankAccount",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("account_name", models.CharField(max_length=200)),
                ("account_number", models.CharField(max_length=20, unique=True)),
                (
                    "bank",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="accounts",
                        to="BackendBil.bank",
                    ),
                ),
                (
                    "system_name",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="BackendBil.system",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="DailyReportBankStatement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("tran_date", models.DateField(null=True)),
                ("voucher_no", models.CharField(max_length=240, null=True)),
                ("instrument_number", models.CharField(max_length=200, null=True)),
                ("instrument_date", models.DateField(null=True)),
                (
                    "credit_amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=20, null=True
                    ),
                ),
                (
                    "debit_amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=20, null=True
                    ),
                ),
                ("status", models.CharField(default="Pending", max_length=50)),
                (
                    "bank_account_number",
                    models.CharField(blank=True, max_length=40, null=True),
                ),
                ("daily_uploaded", models.DateTimeField(auto_now_add=True)),
                (
                    "system_name",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="BackendBil.system",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="BackendBil.user",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="BankStatement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateField(null=True)),
                ("journal_number", models.CharField(max_length=500, null=True)),
                ("rr_number", models.CharField(blank=True, max_length=1000, null=True)),
                (
                    "instrument_number",
                    models.CharField(blank=True, max_length=400, null=True),
                ),
                (
                    "reference_no",
                    models.CharField(blank=True, max_length=400, null=True),
                ),
                (
                    "transaction_type",
                    models.CharField(blank=True, max_length=60, null=True),
                ),
                (
                    "debit",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=20, null=True
                    ),
                ),
                (
                    "credit",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=20, null=True
                    ),
                ),
                (
                    "balance",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=20, null=True
                    ),
                ),
                (
                    "bank_account_number",
                    models.CharField(blank=True, max_length=40, null=True),
                ),
                ("status", models.CharField(default="Pending", max_length=50)),
                ("bankstatement_uploaded", models.DateTimeField(auto_now_add=True)),
                (
                    "bank_name",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="BackendBil.bank",
                    ),
                ),
                (
                    "system_name",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="BackendBil.system",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="BackendBil.user",
                    ),
                ),
            ],
            options={
                "unique_together": {("date", "journal_number")},
            },
        ),
    ]
