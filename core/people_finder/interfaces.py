from abc import ABC, abstractmethod
from typing import List, TypedDict

from core.people_finder.search import get_search_results
from core.people_finder.search_legacy import (
    get_search_results as get_legacy_search_results,
)


class PersonDetail(TypedDict):
    image: str
    first_name: str
    last_name: str
    job_title: str
    directorate: str
    email: str
    phone: str
    grade: str


class PeopleFinderBase(ABC):
    @abstractmethod
    def get_search_results(self, *, search_term: str) -> List[PersonDetail]:
        raise NotImplementedError


class PeopleFinderStubbed(PeopleFinderBase):
    def get_search_results(self, search_term: str) -> List[PersonDetail]:
        return [
            {
                "first_name": "Joe",  # /PS-IGNORE
                "last_name": "Bloggs",
                "image": "",
                "job_title": "Job title",
                "directorate": "Directorate name",
                "email": "joe.bloggs@example.com",  # /PS-IGNORE
                "phone": "0123456789",
                "grade": "Example Grade",
                "image": "",
            },
        ]


class PeopleFinder(PeopleFinderBase):
    def get_search_results(self, search_term: str) -> List[PersonDetail]:
        search_results = get_search_results(search_term)
        results: List[PersonDetail] = []
        for search_result in search_results:
            job_title = ""
            directorate = ""
            if "roles" in search_result and len(search_result["roles"]) > 0:
                job_title = search_result["roles"][0]["job_title"]
                directorate = search_result["roles"][0]["team"]["name"]
            image: str = ""
            if search_result["photo"] is not None:
                image = search_result["photo"]

            results.append(
                {
                    "first_name": search_result["first_name"],
                    "last_name": search_result["last_name"],
                    "image": image,
                    "job_title": job_title,
                    "directorate": directorate,
                    "email": search_result["email"],
                    "phone": search_result["primary_phone_number"],
                    "grade": search_result["grade"],
                }
            )
        return results


class PeopleFinderLegacy(PeopleFinderBase):
    def get_search_results(self, search_term: str) -> List[PersonDetail]:
        search_results = get_legacy_search_results(search_term)

        results = []
        for hit in search_results.hits:
            personal_detail: PersonDetail = {
                "first_name": hit["name"],
                "last_name": hit["name"],
                "image": "",
                "job_title": hit["role_and_group"],
                "directorate": "",
                "email": hit["contact_email_or_email"],
                "phone": hit["phone_number_variations"],
                "grade": "",
            }
            results.append(personal_detail)

        return results
