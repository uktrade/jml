from abc import ABC, abstractmethod
from typing import Optional, TypedDict

from django.http.request import HttpRequest

from core.people_finder.search_legacy import (
    get_search_results as get_legacy_search_results,
)
from core.people_finder.search import (
    get_search_results,
)


class PersonDetail(TypedDict):
    image: str
    name: str
    job_title: str
    email: str
    phone: str


class PeopleFinderBase(ABC):
    @abstractmethod
    def get_search_results(self, *, search_term: str) -> Optional[PersonDetail]:
        raise NotImplementedError


class PeopleFinderStubbed(PeopleFinderBase):
    def get_search_results(self, search_term: str) -> Optional[PersonDetail]:
        return {
            "name": "Joe Bloggs",
        }


class PeopleFinder(PeopleFinderBase):
    def get_search_results(self, search_term: str) -> Optional[PersonDetail]:
        return get_search_results(search_term)


class PeopleFinderLegacy(PeopleFinderBase):
    def get_search_results(self, search_term: str) -> Optional[PersonDetail]:
        search_results = get_legacy_search_results(search_term)

        results = []
        for hit in search_results.hits:
            results.append(
                PersonDetail(
                    #image=hit["image"],
                    name=hit["name"],
                    job_title=hit["role_and_group"],
                    email=hit["contact_email_or_email"],
                    phone=hit["phone_number_variations"],
                )
            )

        return results
