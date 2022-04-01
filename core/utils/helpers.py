from typing import Literal, Optional


def bool_to_yes_no(value: Optional[bool] = None) -> Literal["yes", "no"]:
    if value:
        return "yes"
    return "no"
