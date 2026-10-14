"""`manage.py run_derivations --due` — the schedule of calculated tables.

Run from `CRONJOBS` (the module's settings patch). ⚠ `manage.py crontab add`
runs at container boot: a module installed afterwards is inert on its schedule
until the backend restarts, which is why the installer reports
`derivation_schedule_requires_restart`.
"""
from django.core.management.base import BaseCommand

from migratis.derive import runner


class Command(BaseCommand):
    help = 'Run calculated tables: every scheduled one that is due, or one by name.'

    def add_arguments(self, parser):
        parser.add_argument('--due', action='store_true')
        parser.add_argument('--name', default='')
        parser.add_argument('--anchor', default=None)

    def handle(self, *args, **options):
        if options['name']:
            result = runner.run(options['name'], anchor_id=options['anchor'], trigger='manual')
            self.stdout.write(f"{options['name']}: {result['diff']}")
        elif options['due']:
            self.stdout.write(f'{runner.run_due()} calculated table(s) run.')
        else:
            self.stdout.write('Nothing to do: pass --due or --name.')
