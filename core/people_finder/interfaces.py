from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Optional

from core.people_finder.client import (
    FailedToGetPersonRecord,
    PeopleFinderIterator,
    Person,
    get_details,
)


@dataclass
class PersonDetail:
    sso_user_id: Optional[str]
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
    # TODO: Add support for using the modern sso user id to people finder and switch
    # this interface to use that instead.
    @abstractmethod
    def get_details(self, *, sso_legacy_user_id: str) -> PersonDetail:
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> Iterable[PersonDetail]:
        raise NotImplementedError


class PeopleFinderStubbed(PeopleFinderBase):
    def get_details(self, sso_legacy_user_id: str) -> PersonDetail:
        return PersonDetail(
            sso_user_id="joe.bloggs-31706c8a@example.com",  # /PS-IGNORE
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
                    sso_user_id="joe.bloggs-31706c8a@example.com",  # /PS-IGNORE
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
                    sso_user_id="joe.bloggs-31706c8a@example.com",  # /PS-IGNORE
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

        return self._convert_to_person_detail(person)

    def get_all(self) -> Iterable[PersonDetail]:
        for person in PeopleFinderIterator():
            yield self._convert_to_person_detail(person)

    @staticmethod
    def _convert_to_person_detail(person: Person) -> PersonDetail:
        job_title = ""
        directorate = ""

        if "roles" in person and len(person["roles"]) > 0:
            job_title = person["roles"][0]["role"]
            directorate = person["roles"][0]["team_name"]

        return PersonDetail(
            sso_user_id=person["sso_user_id"],
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
