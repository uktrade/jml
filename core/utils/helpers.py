from typing import Literal


def bool_to_yes_no(value: bool) -> Literal["yes", "no"]:
    if value:
        return "yes"
    return "no"
