"""Credits become fractionable.

Integer -> Decimal(2 places). Postgres widens int to numeric in place, so every
existing balance and price survives with the same value (7 becomes 7.00) and no
row moves.

A whole credit is too coarse a unit once the price of an operation depends on
which model served it: the same call can cost a fraction of a credit on a cheap
model and several on an expensive one, and rounding both to 1 would overcharge
the cheap ones by an order of magnitude. Ported from the migratis generator,
where that per-model pricing lives; the `credits` app itself stays
model-agnostic and only ever applies a multiplier its caller hands it.
"""

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credits', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='creditbalance',
            name='credits',
            field=models.DecimalField(decimal_places=2, default=Decimal('10.00'), max_digits=12),
        ),
        migrations.AlterField(
            model_name='creditcost',
            name='credits',
            field=models.DecimalField(
                decimal_places=2, default=Decimal('1.00'), max_digits=8,
                help_text='Credits deducted per operation, before any per-model coefficient',
            ),
        ),
    ]
