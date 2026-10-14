"""The run log (SCOPE_calculated_tables.md §6.5, D9).

One table, in this module, used by both hosts — the design sandbox and every
generated application — rather than a generator table for one and a module
table for the other, which would be two shapes of one fact. It is
**string-keyed** (application, derivation, anchor) because this module must
never import `generator`: in the sandbox the keys are generator row ids, in a
generated application they are the derivation's name and the anchor's pk.

It is what the calculated tab's strip and `/readiness` read, and —
incidentally — the record of what a forecast said on a given day.
"""
from django.db import models


class DerivationRun(models.Model):
    STATUS_OK = 'ok'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [(STATUS_OK, 'Succeeded'), (STATUS_FAILED, 'Refused')]

    id = models.AutoField(primary_key=True)
    application_key = models.CharField(max_length=64, db_index=True)
    derivation_key = models.CharField(max_length=128)
    anchor_key = models.CharField(
        max_length=64, blank=True, default='',
        help_text="The anchor record's id; blank for an anchorless set.")
    host = models.CharField(max_length=20, default='app',
                            help_text="'sandbox' or 'app'.")
    trigger = models.CharField(max_length=20, default='manual')
    runner = models.CharField(max_length=120, blank=True, default='',
                              help_text="The role (and persona) that pressed the button.")
    as_of = models.DateField(null=True, blank=True,
                             help_text="`today` for this run, fixed once and recorded.")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    error_code = models.CharField(max_length=80, blank=True, default='')
    error = models.TextField(blank=True, default='')
    step_counts = models.JSONField(default=dict, blank=True,
                                   help_text="Rows produced by every input slot and step.")
    skipped = models.JSONField(default=dict, blank=True)
    created = models.PositiveIntegerField(default=0)
    updated = models.PositiveIntegerField(default=0)
    deleted = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(
        default=0, help_text="Rows in the set after the run.")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-id']
        indexes = [models.Index(
            fields=['application_key', 'derivation_key', 'anchor_key'],
            name='derive_run_key_idx')]

    def __str__(self):
        return (f"{self.derivation_key}@{self.anchor_key or '-'} "
                f"{self.status} {self.started_at:%Y-%m-%d %H:%M}")

    @classmethod
    def last(cls, application_key, derivation_key, anchor_key=None, status=None):
        qs = cls.objects.filter(application_key=str(application_key),
                                derivation_key=str(derivation_key))
        if anchor_key is not None:
            qs = qs.filter(anchor_key=str(anchor_key))
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-id').first()
