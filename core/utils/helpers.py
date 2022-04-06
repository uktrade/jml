from typing import Dict, Iterable, List, Literal, Optional, Type

from django.db.models import Model, QuerySet


def bool_to_yes_no(value: Optional[bool] = None) -> Literal["yes", "no"]:
    if value:
        return "yes"
    return "no"


def queryset_to_specific(initial_queryset: QuerySet) -> Iterable[Type[Model]]:
    """
    Convert a Queryset to a list of specific models.

    Only use this on an already filtered queryset (after it has been paginated).
    """

    initial_pks = initial_queryset.values_list("pk", flat=True)

    subclasses = initial_queryset.model.__subclasses__()
    subclass_pks: Dict[Type[Model], List[str]] = {}
    subclass_objects: Dict[int, Type[Model]] = {}

    for subclass in subclasses:
        subclass_queryset = subclass.objects.filter(pk__in=initial_pks)
        subclass_objects |= {obj.pk: obj for obj in subclass_queryset}
        subclass_pks[subclass] = subclass_queryset.values_list("pk", flat=True)

    non_subclass_pks = set(initial_pks) - set(subclass_objects.keys())
    non_subclass_objects: Dict[int, Type[Model]] = {
        obj.pk: obj for obj in initial_queryset.filter(pk__in=non_subclass_pks)
    }

    for init_pk in initial_pks:
        if init_pk in non_subclass_pks:
            yield non_subclass_objects[init_pk]
        else:
            yield subclass_objects[init_pk]
