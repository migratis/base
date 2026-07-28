"""
cookie/management/commands/seed_cookies.py
------------------------------------------
Seeds the cookie inventory published on /cookies.

The list mirrors what https://migratis.ai actually drops on a visitor's device:

    i18next        chosen navigation language (i18next-browser-languagedetector)
    spcc1          cookie-consent acknowledgement (react-cookie-consent)
    csrftoken      Django CSRF protection token
    sessionid      Django authenticated session (HttpOnly)
    __stripe_mid   Stripe fraud prevention, set when the checkout script loads
    __stripe_sid   Stripe checkout session

Descriptions are not stored here — Cookie.description points at the
TranslationKey of the same name in the 'cookie' namespace, which
`seed_translations` owns. Run that first.

Usage:
    python manage.py seed_cookies
    python manage.py seed_cookies --update   # refresh the provider of existing rows

Safe to re-run -- keyed on the cookie name.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from migratis.cookie.models import Cookie
from migratis.i18n.models import TranslationKey

MIGRATIS = 'Migratis'
STRIPE = 'Stripe'

# (cookie name, provider). The description key is the cookie name itself —
# that is also what the frontend looks up, see common/components/Cookies.js.
COOKIES = [
    ('i18next', MIGRATIS),
    ('spcc1', MIGRATIS),
    ('csrftoken', MIGRATIS),
    ('sessionid', MIGRATIS),
    ('__stripe_mid', STRIPE),
    ('__stripe_sid', STRIPE),
]


class Command(BaseCommand):
    help = "Seed the published cookie inventory (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='Overwrite the provider of cookies that already exist.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        update = options['update']
        created_count = 0
        updated_count = 0
        skipped_count = 0
        missing = []

        for name, provider in COOKIES:
            description = TranslationKey.objects.filter(
                key=name, ns__ns='cookie'
            ).first()
            if description is None:
                missing.append(name)
                continue

            cookie = Cookie.objects.filter(name=name).first()
            if cookie is None:
                cookie = Cookie(name=name, provider=provider, description=description)
                cookie.full_clean()
                cookie.save()
                created_count += 1
            elif update:
                cookie.provider = provider
                cookie.description = description
                cookie.full_clean()
                cookie.save()
                updated_count += 1
            else:
                skipped_count += 1

        for name in missing:
            self.stdout.write(self.style.WARNING(
                f"  WARNING: no '{name}' key in the 'cookie' namespace — "
                f"run seed_translations --ns cookie first"
            ))

        self.stdout.write(self.style.SUCCESS(
            'Done.\n'
            '  Cookies created: ' + str(created_count) + '\n' +
            '  Cookies updated: ' + str(updated_count) + '\n' +
            '  Cookies skipped: ' + str(skipped_count) + ' (run with --update to refresh)'
        ))
