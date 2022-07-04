from abc import ABC, abstractmethod
from typing import Iterable, Optional, TypedDict

from core.people_finder.client import (
    FailedToGetPeopleRecords,
    PeopleFinderIterator,
    get_details,
)


class Person(TypedDict):
    first_name: str
    last_name: str
    job_title: str
    directorate: str
    email: str
    phone: str
    grade: str
    photo: Optional[str]
    photo_small: Optional[str]


class PeopleFinderBase(ABC):
    @abstractmethod
    def get_details(self, *, legacy_sso_user_id: str) -> Person:
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> Iterable[Person]:
        raise NotImplementedError


class PeopleFinderStubbed(PeopleFinderBase):
    def get_details(self, legacy_sso_user_id: str) -> Person:
        return {
            "first_name": "Joe",  # /PS-IGNORE
            "last_name": "Bloggs",
            "job_title": "Job title",
            "directorate": "Directorate name",
            "email": "joe.bloggs@example.com",  # /PS-IGNORE
            "phone": "0123456789",
            "grade": "Example Grade",
            "photo": "",
            "photo_small": "",
        }

    def get_all(self) -> Iterable[Person]:
        return iter(
            [
                {
                    "first_name": "Joe",  # /PS-IGNORE
                    "last_name": "Bloggs",
                    "job_title": "Job title",
                    "directorate": "Directorate name",
                    "email": "joe.bloggs@example.com",  # /PS-IGNORE
                    "phone": "0123456789",
                    "grade": "Example Grade",
                    "photo": "",
                    "photo_small": "",
                },
                {
                    "first_name": "Jane",  # /PS-IGNORE
                    "last_name": "Doe",
                    "job_title": "Job title",
                    "directorate": "Directorate name",
                    "email": "jane.doe@example.com",  # /PS-IGNORE
                    "phone": "0987654321",
                    "grade": "Example Grade",
                    "photo": "",
                    "photo_small": "",
                },
            ]
        )


class PeopleFinderPersonNotFound(Exception):
    pass


class PeopleFinder(PeopleFinderBase):
    def get_details(self, legacy_sso_user_id: str) -> Person:
        try:
            person = get_details(legacy_sso_user_id)
        except FailedToGetPeopleRecords:
            raise PeopleFinderPersonNotFound()

        job_title = ""
        directorate = ""

        if "roles" in person and len(person["roles"]) > 0:
            job_title = person["roles"][0]["role"]
            directorate = person["roles"][0]["team_name"]

        return {
            "first_name": person["first_name"],
            "last_name": person["last_name"],
            "job_title": job_title,
            "directorate": directorate,
            "email": person["email"],
            "phone": person["primary_phone_number"],
            "grade": person["grade"],
            "photo": person["photo"],
            "photo_small": person["photo_small"],
        }

    def get_all(self) -> Iterable[Person]:
        return PeopleFinderIterator()
