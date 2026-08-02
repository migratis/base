from ninja import ModelSchema

from . import models


class InvoiceSchema(ModelSchema):
    """A receipt for any paying purpose. `purpose` is what lets Account →
    Billing file each invoice under the module that produced it (credits vs
    subscription) without either module owning the endpoint."""

    class Meta:
        model = models.Invoice
        fields = ['id', 'purpose', 'reference', 'label_key',
                  'cdate', 'mdate', 'status', 'amount']
