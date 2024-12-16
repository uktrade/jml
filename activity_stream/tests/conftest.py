import datetime
from uuid import uuid4

import pytest
from factory.faker import faker


@pytest.fixture
def sso_user_factory():
    def _factory():
        factory_faker = faker.Faker()

        id = str(uuid4())
        first_name = factory_faker.first_name()
        last_name = factory_faker.last_name()
        return {
            "published": datetime.datetime.today().strftime("%Y%m%dT%H%M%S.%dZ"),
            "object": {
                "id": f"dit:StaffSSO:User:{id}",
                "dit:StaffSSO:User:userId": id,
                "dit:emailAddress": [factory_faker.email(), factory_faker.email()],
                "dit:firstName": first_name,
                "dit:lastName": last_name,
                "name": factory_faker.name(),
                "type": "dit:StaffSSO:User",
                "dit:StaffSSO:User:status": "active",
                "dit:StaffSSO:User:joined": datetime.datetime.today().strftime(
                    "%Y%m%dT%H%M%S.%dZ"
                ),
                "dit:StaffSSO:User:lastAccessed": (
                    datetime.datetime.today().strftime("%Y%m%dT%H%M%S.%dZ")
                ),
                "dit:StaffSSO:User:emailUserId": (
                    f"{first_name}.{last_name}-2b11c60l@id.trade.gov.uk"
                ),
                "dit:StaffSSO:User:becameInactiveOn": None,
                "dit:StaffSSO:User:contactEmailAddress": None,
            },
        }

    return _factory
