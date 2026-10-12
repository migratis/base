"""
cookie/management/commands/seed_cookies.py
------------------------------------------
Seeds the inventory published on /cookies.

The list mirrors what https://migratis.ai actually stores on a visitor's
device, and the two halves of "actually" are both load-bearing:

* **It is storage, not cookies.** ePrivacy Art. 5(3) is about storage on
  terminal equipment, so a localStorage key belongs in a cookie disclosure.
  Publishing only the cookies hid four entries and misdescribed a fifth: the
  ``i18next`` cookie expires in ten minutes (``frontend/src/i18n.js``,
  ``cookieMinutes: 10``) while the language the site remembers for real lives
  in ``i18nextLng``, which was declared nowhere.

* **It is what we set, not what our suppliers set.** ``__stripe_mid`` and
  ``__stripe_sid`` used to be in here. Migratis uses Stripe's *hosted*
  Checkout — ``stripe_payment/views.py`` answers a ``checkout_url`` and
  ``Subscribe.js`` sends the browser to it — and ``@stripe/stripe-js`` is a
  declared dependency that is imported nowhere, so no Stripe script ever runs
  on migratis.ai and neither cookie is ever set on this domain. They are
  Stripe's, set on Stripe's, disclosed by Stripe. Declaring them told the
  reader we store something we do not, and (worse) invited a consent
  mechanism for storage that is out of our reach. Run with ``--prune`` to
  retire them from a database that still carries them.

Every entry here is ``necessary``, which is why the first-visit banner is an
information notice and not a consent request: migratis.ai runs no analytics,
serves no advertising and loads no third-party script. ``tests.py`` asserts it,
so the day a non-exempt entry is added the suite says what else has to change.

Descriptions are not stored here — ``Cookie.description`` points at the
``TranslationKey`` of the same name in the 'cookie' namespace, which
``seed_translations`` owns. Run that first.

Usage:
    python manage.py seed_cookies
    python manage.py seed_cookies --update   # refresh the declaration of existing rows
    python manage.py seed_cookies --prune    # retire rows this file no longer declares

Safe to re-run -- keyed on the entry name.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from migratis.cookie.models import Cookie
from migratis.i18n.models import TranslationKey

MIGRATIS = 'Migratis'

# The description key is the entry name itself — that is also what the frontend
# looks up, see common/components/Cookies.js.
COOKIES = [
    # ── Authentication and security ──────────────────────────────────────────
    {
        'name': 'sessionid',
        'provider': MIGRATIS,
        'storage': Cookie.STORAGE_COOKIE,
        'category': Cookie.CATEGORY_NECESSARY,
        # settings.SESSION_COOKIE_AGE = 14400
        'retention_unit': Cookie.RETENTION_HOURS,
        'retention_value': 4,
    },
    {
        'name': 'csrftoken',
        'provider': MIGRATIS,
        'storage': Cookie.STORAGE_COOKIE,
        'category': Cookie.CATEGORY_NECESSARY,
        # Django's CSRF_COOKIE_AGE default, unchanged in settings.py.
        'retention_unit': Cookie.RETENTION_MONTHS,
        'retention_value': 12,
    },
    {
        'name': 'user',
        'provider': MIGRATIS,
        'storage': Cookie.STORAGE_LOCAL,
        'category': Cookie.CATEGORY_NECESSARY,
        'retention_unit': Cookie.RETENTION_PERSISTENT,
    },
    {
        'name': 'session_expired',
        'provider': MIGRATIS,
        'storage': Cookie.STORAGE_LOCAL,
        'category': Cookie.CATEGORY_NECESSARY,
        'retention_unit': Cookie.RETENTION_PERSISTENT,
    },
    # ── The visitor's own choices ────────────────────────────────────────────
    {
        'name': 'i18next',
        'provider': MIGRATIS,
        'storage': Cookie.STORAGE_COOKIE,
        'category': Cookie.CATEGORY_NECESSARY,
        # frontend/src/i18n.js, detection.cookieMinutes
        'retention_unit': Cookie.RETENTION_MINUTES,
        'retention_value': 10,
    },
    {
        'name': 'i18nextLng',
        'provider': MIGRATIS,
        'storage': Cookie.STORAGE_LOCAL,
        'category': Cookie.CATEGORY_NECESSARY,
        'retention_unit': Cookie.RETENTION_PERSISTENT,
    },
    {
        # The record of the visitor's answer to the storage notice. Exempt
        # because its only purpose is to stop us asking again, which is the
        # service they requested by answering. It replaces `spcc1`, whose
        # value recorded an acceptance obtained by telling the reader that
        # continuing to browse was agreement — see
        # common/tools/cookieConsent.js.
        'name': 'mg_consent',
        'provider': MIGRATIS,
        'storage': Cookie.STORAGE_COOKIE,
        'category': Cookie.CATEGORY_NECESSARY,
        'retention_unit': Cookie.RETENTION_MONTHS,
        'retention_value': 6,
    },
    # ── Keeping the application loadable ─────────────────────────────────────
    {
        'name': 'page-has-been-force-refreshed',
        'provider': MIGRATIS,
        'storage': Cookie.STORAGE_LOCAL,
        'category': Cookie.CATEGORY_NECESSARY,
        'retention_unit': Cookie.RETENTION_PERSISTENT,
    },
]

DECLARED_NAMES = {entry['name'] for entry in COOKIES}


class Command(BaseCommand):
    help = "Seed the published storage inventory (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='Overwrite the declaration of entries that already exist.',
        )
        parser.add_argument(
            '--prune',
            action='store_true',
            help='Retire rows this file no longer declares. An inventory that '
                 'over-declares is as wrong as one that under-declares.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        update = options['update']
        created_count = 0
        updated_count = 0
        skipped_count = 0
        missing = []

        for entry in COOKIES:
            name = entry['name']
            description = TranslationKey.objects.filter(
                key=name, ns__ns='cookie'
            ).first()
            if description is None:
                missing.append(name)
                continue

            cookie = Cookie.objects.filter(name=name).first()
            if cookie is None:
                cookie = Cookie(name=name, description=description)
                self._apply(cookie, entry)
                created_count += 1
            elif update:
                cookie.description = description
                self._apply(cookie, entry)
                updated_count += 1
            else:
                skipped_count += 1

        pruned = []
        if options['prune']:
            stale = Cookie.objects.exclude(name__in=DECLARED_NAMES)
            pruned = sorted(stale.values_list('name', flat=True))
            stale.delete()

        for name in missing:
            self.stdout.write(self.style.WARNING(
                f"  WARNING: no '{name}' key in the 'cookie' namespace — "
                f"run seed_translations --ns cookie first"
            ))

        for name in pruned:
            self.stdout.write(self.style.WARNING(
                f"  RETIRED: '{name}' is no longer declared and has been "
                f"removed from the published inventory"
            ))

        if not options['prune']:
            undeclared = Cookie.objects.exclude(
                name__in=DECLARED_NAMES
            ).values_list('name', flat=True)
            for name in sorted(undeclared):
                self.stdout.write(self.style.WARNING(
                    f"  UNDECLARED: '{name}' is published but this file no "
                    f"longer declares it — run with --prune to retire it"
                ))

        self.stdout.write(self.style.SUCCESS(
            'Done.\n'
            '  Entries created: ' + str(created_count) + '\n' +
            '  Entries updated: ' + str(updated_count) + '\n' +
            '  Entries skipped: ' + str(skipped_count) + ' (run with --update to refresh)\n' +
            '  Entries retired: ' + str(len(pruned))
        ))

    @staticmethod
    def _apply(cookie, entry):
        cookie.provider = entry['provider']
        cookie.storage = entry['storage']
        cookie.category = entry['category']
        cookie.retention_unit = entry['retention_unit']
        cookie.retention_value = entry.get('retention_value')
        cookie.full_clean()
        cookie.save()
