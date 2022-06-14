from abc import ABC, abstractmethod
from typing import List, TypedDict

from core.people_finder.person import get_details



class Person(TypedDict):
    first_name: str
    last_name: str
    job_title: str
    directorate: str
    email: str
    phone: str
    grade: str
    photo: str
    photo_small: str


class PeopleFinderBase(ABC):
    @abstractmethod
    def get_details(self, *, legacy_sso_user_id: str) -> Person:
        raise NotImplementedError


class PeopleFinderStubbed(PeopleFinderBase):
    def get_details(self, legacy_sso_user_id: str) -> Person:
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
                "photo": "",
                "photo_small": "",
            },
        ]


class PeopleFinder(PeopleFinderBase):
    def get_details(self, legacy_sso_user_id: str) -> Person:

        person = get_details(legacy_sso_user_id)

        job_title = ""
        directorate = ""

        if "roles" in person and len(person["roles"]) > 0:
            job_title = person["roles"][0]["job_title"]
            directorate = person["roles"][0]["team"]["name"]

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
