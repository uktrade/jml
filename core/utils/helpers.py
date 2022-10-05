from enum import Enum
from typing import Dict, Iterable, List, Literal, Optional, Type

from django.db.models import Model, QuerySet
from django.utils import timezone


class IsoWeekdays(Enum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


def bool_to_yes_no(value: Optional[bool] = None) -> Literal["yes", "no"]:
    if value:
        return "yes"
    return "no"


def yes_no_to_bool(value: Literal["yes", "no"]) -> bool:
    if value == "yes":
        return True
    elif value == "no":
        return False
    raise ValueError("Invalid value for yes_no_to_bool")


def is_work_day_and_time() -> bool:
    """
    Returns True if it is a work day and during working hours.
    """

    now = timezone.now()
    today = now.date()
    if today.isoweekday() in [
        IsoWeekdays.SATURDAY.value,
        IsoWeekdays.SUNDAY.value,
    ]:
        return False

    # Check to see if the time is between 9-5.
    if now.hour >= 9 and now.hour <= 17:
        return True
    return False


def make_possessive(word: str) -> str:
    if word.endswith("s"):
        return word + "'"
    return word + "'s"


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
        subclass_queryset: QuerySet = subclass.objects.filter(pk__in=initial_pks)
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
