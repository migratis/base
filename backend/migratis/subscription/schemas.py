from ninja import ModelSchema
from . import models
from migratis.i18n.schemas import TranslationKeySchema

class PlanSchema(ModelSchema):
    label: TranslationKeySchema
    class Meta:
        model = models.Plan
        fields = ['id', 'label', 'price', 'life']

class SubscriptionSchema(ModelSchema):
    plan: PlanSchema | None = None

    class Meta:
        model = models.Subscription
        fields = ['plan', 'access', 'status', 'end', 'cancelled']

class InvoiceSchema(ModelSchema):
    class Meta:
        model = models.Invoice
        fields = ['id', 'purpose', 'reference', 'label_key', 'cdate', 'mdate', 'status', 'amount']
