from django.db.models import Case, IntegerField, Value, When
from django.http import JsonResponse
from typing import List
from ninja import Router
from migratis.api.functions import formatErrors
from . import models, schemas

router = Router()


def _category_rank():
    """Publish strictly-necessary storage first, then in increasing order of
    intrusiveness. Alphabetical ordering would open the page on 'marketing'."""
    return Case(
        *[
            When(category=category, then=Value(rank))
            for rank, category in enumerate(models.Cookie.CATEGORY_ORDER)
        ],
        default=Value(len(models.Cookie.CATEGORY_ORDER)),
        output_field=IntegerField(),
    )


@router.get('/list/', response=List[schemas.CookieSchema], auth=None)
def getCookiesList(request):
    """The published inventory behind /cookies.

    What this answers is the disclosure. It is deliberately the same for every
    reader: the page used to merge whatever `document.cookie` happened to hold
    into the same table, with an empty provider and an empty purpose, which
    made a legal document read differently per visitor and listed entries it
    could not explain.
    """
    cookies = models.Cookie.objects.annotate(
        category_rank=_category_rank()
    ).order_by('category_rank', 'storage', 'name')

    if cookies is not None:
        return cookies

    return JsonResponse({"detail": formatErrors({"cookie": ["cookie-not-exists"]})}, status=422)
