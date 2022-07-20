from typing import TypedDict


class Address(TypedDict):
    # See: https://design-system.service.gov.uk/patterns/addresses/multiple/index.html
    # We can alter this based on what data we take from the form and how
    # Service Now expects the data.
    line_1: str
    line_2: str
    town_or_city: str
    county: str
    postcode: str
