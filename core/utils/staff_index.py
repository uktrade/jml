from typing import Any, List, Mapping, TypedDict, cast

from django.conf import settings
from opensearch_dsl import Search
from opensearchpy import OpenSearch
from opensearchpy.exceptions import NotFoundError

MAX_RESULTS = 100
MIN_SCORE = 0.02

HOST_URLS: List[str] = settings.SEARCH_HOST_URLS
STAFF_INDEX_NAME: str = settings.SEARCH_STAFF_INDEX_NAME
STAFF_INDEX_BODY: Mapping[str, Any] = {
    "mappings": {
        "properties": {
            "staff_sso_activity_stream_id": {"type": "text"},
            "staff_sso_first_name": {"type": "text"},
            "staff_sso_last_name": {"type": "text"},
            "staff_sso_email_address": {"type": "text"},
            "staff_sso_contact_email_address": {"type": "text"},
        },
    },
}


class StaffDocument(TypedDict):
    staff_sso_activity_stream_id: str
    staff_sso_first_name: str
    staff_sso_last_name: str
    staff_sso_email_address: str
    staff_sso_contact_email_address: str


def get_search_connection() -> OpenSearch:
    if not HOST_URLS:
        raise Exception("Elasticsearch hosts not configured")
    return OpenSearch(HOST_URLS)


def create_staff_index():
    search_client = get_search_connection()
    search_client.indices.create(index=STAFF_INDEX_NAME, body=STAFF_INDEX_BODY)


def delete_staff_index():
    """
    Delete the entire index.
    """
    search_client = get_search_connection()
    search_client.indices.delete(index=STAFF_INDEX_NAME)


def clear_staff_index():  # /PS-IGNORE
    """
    Delete all documents from the index.
    """
    search_client = get_search_connection()
    search_client.delete_by_query(
        index=STAFF_INDEX_NAME,
        body={"query": {"match_all": {}}},
        ignore=400,
    )


class StaffIndexNotFound(Exception):
    pass


def staff_index_mapping_changed() -> bool:
    """
    Check to see if the existing mapping and our expected mapping differ.
    """
    staff_index_mapping = STAFF_INDEX_BODY["mappings"]
    search_client = get_search_connection()
    try:
        mappings = search_client.indices.get_mapping(index=STAFF_INDEX_NAME)
    except NotFoundError:
        raise StaffIndexNotFound()
    current_mapping = mappings.get(STAFF_INDEX_NAME, {}).get("mappings", {})
    return current_mapping != staff_index_mapping


def index_staff_document(*, staff_document: StaffDocument):
    """
    Add a Staff document to the Staff index.
    """
    search_client = get_search_connection()
    search_client.index(
        index=STAFF_INDEX_NAME,
        body=staff_document,
    )


def search_staff_index(*, query: str) -> List[StaffDocument]:
    """
    Search the Staff index.
    """
    search_client = get_search_connection()
    search_dict = {
        "query": {
            "bool": {
                "should": [
                    {"match": {"staff_sso_first_name": {"query": query, "boost": 6.0}}},
                    {"match": {"staff_sso_last_name": {"query": query, "boost": 6.0}}},
                    {"multi_match": {"query": query, "analyzer": "standard"}},
                ],
                "minimum_should_match": 1,
                "boost": 1.0,
            }
        },
        "sort": {
            "_score": {"order": "desc"},
        },
        "size": MAX_RESULTS,
        "min_score": MIN_SCORE,
    }

    search = (
        Search(index=STAFF_INDEX_NAME)
        .using(search_client)
        .update_from_dict(search_dict)
    )
    search_results = search.execute()

    staff_documents = []
    for hit in search_results.hits:
        staff_document = cast(
            StaffDocument,
            {
                field_name: hit[field_name]
                for field_name in StaffDocument.__annotations__
            },
        )
        staff_documents.append(staff_document)

    return staff_documents
