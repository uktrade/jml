from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Optional

from core.people_finder.client import (
    FailedToGetPersonRecord,
    PeopleFinderIterator,
    get_details,
)


@dataclass
class PersonDetail:
    first_name: str
    last_name: str
    job_title: str
    directorate: str
    email: str
    phone: Optional[str]
    grade: Optional[str]
    photo: Optional[str]
    photo_small: Optional[str]


class PeopleFinderBase(ABC):
    @abstractmethod
    def get_details(self, *, sso_legacy_user_id: str) -> PersonDetail:
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> Iterable[PersonDetail]:
        raise NotImplementedError


class PeopleFinderStubbed(PeopleFinderBase):
    def get_details(self, sso_legacy_user_id: str) -> PersonDetail:
        return PersonDetail(
            first_name="Joe",  # /PS-IGNORE
            last_name="Bloggs",
            job_title="Job title",
            directorate="Directorate name",
            email="joe.bloggs@example.com",  # /PS-IGNORE
            phone="0123456789",
            grade="Example Grade",
            photo="",
            photo_small="",
        )

    def get_all(self) -> Iterable[PersonDetail]:
        return iter(
            [
                PersonDetail(
                    first_name="Joe",  # /PS-IGNORE
                    last_name="Bloggs",
                    job_title="Job title",
                    directorate="Directorate name",
                    email="joe.bloggs@example.com",  # /PS-IGNORE
                    phone="0123456789",
                    grade="Example Grade",
                    photo="",
                    photo_small="",
                ),
                PersonDetail(
                    first_name="Jane",  # /PS-IGNORE
                    last_name="Doe",
                    job_title="Job title",
                    directorate="Directorate name",
                    email="jane.doe@example.com",  # /PS-IGNORE
                    phone="0987654321",
                    grade="Example Grade",
                    photo="",
                    photo_small="",
                ),
            ]
        )


class PeopleFinderPersonNotFound(Exception):
    pass


class PeopleFinder(PeopleFinderBase):
    def get_details(self, sso_legacy_user_id: str) -> PersonDetail:
        try:
            person = get_details(sso_legacy_user_id)
        except FailedToGetPersonRecord:
            raise PeopleFinderPersonNotFound()

        job_title = ""
        directorate = ""

        if "roles" in person and len(person["roles"]) > 0:
            job_title = person["roles"][0]["role"]
            directorate = person["roles"][0]["team_name"]

        return PersonDetail(
            first_name=person["first_name"],
            last_name=person["last_name"],
            job_title=job_title,
            directorate=directorate,
            email=person["email"],
            phone=person["primary_phone_number"],
            grade=person["grade"],
            photo=person["photo"],
            photo_small=person["photo_small"],
        )

    def get_all(self) -> Iterable[PersonDetail]:
        return PeopleFinderIterator()
