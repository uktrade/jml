from typing import Any, List, Mapping, TypedDict, cast

from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl import Search

ES_MAX_RESULTS = 100
ES_MIN_SCORE = 0.02
ES_PRE_TAGS = '<strong class="ws-person-search-result__highlight">'
ES_POST_TAGS = "</strong>"

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


class StaffIndexNotFound(Exception):
    pass


def staff_index_mapping_changed() -> bool:
    """
    Check to see if the existing mapping and our expected mapping differ.
    """
    es_conn = get_elasticsearch_connection()
    try:
        mappings = es_conn.indices.get_mapping(index=STAFF_INDEX_NAME)
    except NotFoundError:
        raise StaffIndexNotFound()
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


def search_staff_index(*, query: str) -> List[StaffDocument]:
    """
    Search the Staff index.
    """
    es_conn = get_elasticsearch_connection()
    search_dict = {
        "query": {
            "bool": {
                "should": [
                    {"match": {"staff_sso_first_name": {"query": query, "boost": 6.0}}},
                    {"match": {"staff_sso_last_name": {"query": query, "boost": 6.0}}},
                    # TODO: Update "field_name^X" for each of the fields.
                    {
                        "multi_match": {
                            "fields": [
                                "staff_sso_activity_stream_id^1",
                                "staff_sso_first_name^1",
                                "staff_sso_last_name^1",
                                "staff_sso_email_address^1",
                                "staff_sso_contact_email_address^1",
                            ],
                            "query": query,
                            "analyzer": "standard",
                        }
                    },
                ],
                "minimum_should_match": 1,
                "boost": 1.0,
            }
        },
        "sort": {
            "_score": {"order": "desc"},
        },
        "highlight": {
            "pre_tags": ES_PRE_TAGS,
            "post_tags": ES_POST_TAGS,
            "number_of_fragments": 0,
            "fields": {
                "staff_sso_first_name": {},
                "staff_sso_last_name": {},
            },
        },
        "size": ES_MAX_RESULTS,
        "min_score": ES_MIN_SCORE,
    }

    search = Search(index=STAFF_INDEX_NAME).using(es_conn).update_from_dict(search_dict)
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
