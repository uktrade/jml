import requests
import urllib.parse

from mohawk import Sender

from django.conf import settings


CONTENT_TYPE = "application/json"


def search_people_finder(search_term):
    safe_search_term = urllib.parse.quote_plus(search_term)
    url = f"{settings.PEOPLE_FINDER_URL}/api/people-search/?search_query={safe_search_term}"
    sender = Sender(
        {
            'id': settings.HAWK_ACCESS_ID,
            'key': settings.HAWK_SECRET_KEY,
            'algorithm': 'sha256'
        },
        url,
        'GET',
        content="",
        content_type=CONTENT_TYPE,
    )

    response = requests.get(
        url,
        data="",
        headers={
            'Authorization': sender.request_header,
            'Content-Type': CONTENT_TYPE
        }
    )

    return response.json()
