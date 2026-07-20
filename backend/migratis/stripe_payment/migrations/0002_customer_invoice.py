"""Phase 5 — relocate Customer + Invoice into stripe_payment (base lineage).

Same as the migratis migration, but base's subscription app is a single
0001_initial, so the dependency points there. The tables
(``subscription_customer`` / ``subscription_invoice``) are kept in place via
SeparateDatabaseAndState — no data moves; only the Invoice generalization
(nullable subscription/plan, new ``purpose`` / ``payment`` columns) touches the
DB.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stripe_payment', '0001_initial'),
        ('subscription', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='Customer',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('cdate', models.DateTimeField(auto_now_add=True)),
                        ('mdate', models.DateTimeField(auto_now=True)),
                        ('stripe_id', models.CharField(max_length=50)),
                        ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                    ],
                    options={'verbose_name_plural': 'Customers', 'db_table': 'subscription_customer'},
                ),
                migrations.CreateModel(
                    name='Invoice',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('status', models.CharField(default='draft', max_length=20)),
                        ('file', models.FileField(blank=True, null=True, upload_to='migratis/subscription/invoices')),
                        ('stripe_id', models.CharField(max_length=50)),
                        ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=99)),
                        ('tax', models.DecimalField(decimal_places=2, default=0, max_digits=99)),
                        ('cdate', models.DateTimeField(auto_now_add=True)),
                        ('mdate', models.DateTimeField(auto_now=True)),
                        ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                        ('customer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='stripe_payment.customer')),
                        ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='subscription.subscription')),
                        ('plan', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='subscription.plan')),
                    ],
                    options={'verbose_name_plural': 'Invoices', 'db_table': 'subscription_invoice'},
                ),
            ],
            database_operations=[],
        ),
        migrations.AlterField(
            model_name='invoice',
            name='subscription',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='subscription.subscription'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='plan',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='subscription.plan'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='purpose',
            field=models.CharField(default='subscription', max_length=32),
        ),
        migrations.AddField(
            model_name='invoice',
            name='payment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='stripe_payment.stripepayment'),
        ),
    ]
