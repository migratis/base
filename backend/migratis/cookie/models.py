"""
cookie/models.py
----------------
The published inventory behind /cookies.

ePrivacy Article 5(3) is about *storage on terminal equipment*, not about
cookies: a key in localStorage is the same legal act as a cookie, so the
inventory names the ``storage`` mechanism rather than assuming one. And the two
things a disclosure may not omit — what the entry is *for* and how long it
lasts — are columns here (``category``, ``retention_*``) rather than prose
somebody has to remember to keep in step with the code.

``category`` is the whole consent decision. Only ``necessary`` is exempt under
Article 5(3)(b) ("strictly necessary to provide a service explicitly requested
by the user"); every other category must be refusable before it is stored, and
refusable afterwards. ``requires_consent`` is therefore read by the notice, by
the published page and by the test that asserts this deployment still only
stores what it is exempt for.
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from migratis.i18n.models import TranslationKey


class Cookie(models.Model):
    # ── The mechanism ────────────────────────────────────────────────────────
    # Article 5(3) covers any storage on the visitor's device. Publishing only
    # the cookies was the hole: the language this site remembers lives in
    # localStorage (`i18nextLng`) and the cookie beside it expires in ten
    # minutes, so the entry the reader was shown described neither.
    STORAGE_COOKIE = 'cookie'
    STORAGE_LOCAL = 'local_storage'
    STORAGE_SESSION = 'session_storage'
    STORAGE_KINDS = [
        (STORAGE_COOKIE, _('Cookie')),
        (STORAGE_LOCAL, _('Local storage')),
        (STORAGE_SESSION, _('Session storage')),
    ]

    # ── The purpose, and therefore the consent ───────────────────────────────
    CATEGORY_NECESSARY = 'necessary'
    CATEGORY_PREFERENCES = 'preferences'
    CATEGORY_STATISTICS = 'statistics'
    CATEGORY_MARKETING = 'marketing'
    CATEGORIES = [
        (CATEGORY_NECESSARY, _('Strictly necessary')),
        (CATEGORY_PREFERENCES, _('Preferences')),
        (CATEGORY_STATISTICS, _('Statistics')),
        (CATEGORY_MARKETING, _('Marketing')),
    ]
    # Reading order of the published page: what the visitor cannot refuse
    # first, then in increasing order of intrusiveness.
    CATEGORY_ORDER = [
        CATEGORY_NECESSARY,
        CATEGORY_PREFERENCES,
        CATEGORY_STATISTICS,
        CATEGORY_MARKETING,
    ]
    EXEMPT_CATEGORIES = (CATEGORY_NECESSARY,)

    # ── How long it lasts ────────────────────────────────────────────────────
    # A duration is a number and a unit, not a sentence, so it survives being
    # read in four languages. `session` and `persistent` carry no number:
    # a cookie dropped when the tab closes, and a localStorage key that lasts
    # until the visitor clears it, are both honest answers and neither is a
    # count of anything.
    RETENTION_SESSION = 'session'
    RETENTION_PERSISTENT = 'persistent'
    RETENTION_MINUTES = 'minutes'
    RETENTION_HOURS = 'hours'
    RETENTION_DAYS = 'days'
    RETENTION_MONTHS = 'months'
    RETENTION_UNITS = [
        (RETENTION_SESSION, _('Until the browser is closed')),
        (RETENTION_PERSISTENT, _('Until you clear it')),
        (RETENTION_MINUTES, _('Minutes')),
        (RETENTION_HOURS, _('Hours')),
        (RETENTION_DAYS, _('Days')),
        (RETENTION_MONTHS, _('Months')),
    ]
    UNCOUNTED_RETENTION_UNITS = (RETENTION_SESSION, RETENTION_PERSISTENT)

    name = models.CharField(max_length=500, null=False)
    provider = models.CharField(max_length=50, null=False)
    description = models.ForeignKey(
        TranslationKey,
        related_name='translation_cookie_descriptions',
        on_delete=models.PROTECT,
    )
    storage = models.CharField(
        max_length=20, choices=STORAGE_KINDS, default=STORAGE_COOKIE,
        help_text='The mechanism storing it on the visitor’s device. '
                  'ePrivacy Art. 5(3) treats them alike.',
    )
    category = models.CharField(
        max_length=20, choices=CATEGORIES, default=CATEGORY_NECESSARY,
        help_text='Only “strictly necessary” is exempt from consent. Anything '
                  'else must be refusable before it is stored.',
    )
    retention_unit = models.CharField(
        max_length=20, choices=RETENTION_UNITS, default=RETENTION_SESSION,
        help_text='The unit of the retention period, or how it ends when it '
                  'is not a count.',
    )
    retention_value = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='How many of the unit above. Left empty for a retention '
                  'that is not a count.',
    )
    cdate = models.DateTimeField(auto_now_add=True)
    mdate = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "cookies"

    def __str__(self):
        return self.name

    @property
    def requires_consent(self):
        """Whether storing this needs the visitor's permission first.

        The single question the notice, the published page and the inventory
        test all ask. Derived from the category so the answer cannot be stored
        in disagreement with the purpose it follows from.
        """
        return self.category not in self.EXEMPT_CATEGORIES

    def clean(self):
        super().clean()
        counted = self.retention_unit not in self.UNCOUNTED_RETENTION_UNITS
        if counted and self.retention_value is None:
            # "days", with nothing in front of it, is not a retention period —
            # and the retention period is the one thing a disclosure may not
            # leave the reader to guess.
            raise ValidationError({'retention_value': ['retention-value-required']})
        if not counted and self.retention_value is not None:
            raise ValidationError({'retention_value': ['retention-value-not-counted']})
