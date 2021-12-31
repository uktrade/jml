from typing import Any, List, Mapping, TypedDict

from django.conf import settings
from elasticsearch import Elasticsearch

HOST_URLS: List[str] = settings.ELASTIC_SEARCH_HOST_URLS
STAFF_INDEX_NAME: str = settings.ELASTIC_SEARCH_STAFF_INDEX_NAME
STAFF_INDEX_MAPPING: Mapping[str, Any] = {
    "properties": {
        "staff_sso_activity_stream_id": {"type": "text"},
        "staff_sso_first_name": {"type": "text"},
        "staff_sso_last_name": {"type": "text"},
        "staff_sso_email_address": {"type": "text"},
        "staff_sso_contact_email_address": {"type": "text"},
    },
}


class StaffDocument(TypedDict):
    staff_sso_activity_stream_id: str
    staff_sso_first_name: str
    staff_sso_last_name: str
    staff_sso_email_address: str
    staff_sso_contact_email_address: str


def get_elasticsearch_connection():
    if not HOST_URLS:
        raise Exception("Elasticsearch hosts not configured")
    return Elasticsearch(HOST_URLS)


def create_staff_index():
    es_conn = get_elasticsearch_connection()
    es_conn.indices.create(
        index=STAFF_INDEX_NAME, ignore=400, mappings=STAFF_INDEX_MAPPING
    )


def delete_staff_index():
    """
    Delete the entire index.
    """
    es_conn = get_elasticsearch_connection()
    es_conn.indices.delete(index=STAFF_INDEX_NAME, ignore=400)


def clear_staff_index():  # /PS-IGNORE
    """
    Delete all documents from the index.
    """
    es_conn = get_elasticsearch_connection()
    es_conn.delete_by_query(
        index=STAFF_INDEX_NAME,
        body={"query": {"match_all": {}}},
        ignore=400,
    )


def staff_index_mapping_changed() -> bool:
    """
    Check to see if the existing mapping and our expected mapping differ.
    """
    es_conn = get_elasticsearch_connection()
    mappings = es_conn.indices.get_mapping(index=STAFF_INDEX_NAME)
    current_mapping = mappings.get(STAFF_INDEX_NAME, {}).get("mappings", {})
    return current_mapping != STAFF_INDEX_MAPPING


def index_staff_document(*, staff_document: StaffDocument):
    """
    Add a Staff document to the Staff index.
    """
    es_conn = get_elasticsearch_connection()
    es_conn.index(
        index=STAFF_INDEX_NAME,
        body=staff_document,
    )
