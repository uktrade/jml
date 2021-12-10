import factory

from user.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Sequence(lambda n: f"user{n}@example.com")  # /PS-IGNORE
    legacy_sso_user_id = factory.Sequence(lambda n: f"SSO User ID {n}")
    username = factory.Sequence(lambda n: f"user{n}")
    # fmt: off
    sso_contact_email = factory.Sequence(
        lambda n: f"user{n}.contact@example.com",  # /PS-IGNORE
    )
    # fmt: on
