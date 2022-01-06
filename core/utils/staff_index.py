from datetime import date
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
            "people_finder_image": {"type": "text"},
            "people_finder_first_name": {"type": "text"},
            "people_finder_last_name": {"type": "text"},
            "people_finder_job_title": {"type": "text"},
            "people_finder_directorate": {"type": "text"},
            "people_finder_phone": {"type": "text"},
            "people_finder_grade": {"type": "text"},
            "service_now_department_id": {"type": "text"},
            "service_now_department_name": {"type": "text"},
            "service_now_directorate_id": {"type": "text"},
            "ervice_now_directorate_name": {"type": "text"},
        },
    },
}


class StaffDocument(TypedDict):
    staff_sso_activity_stream_id: str
    staff_sso_first_name: str
    staff_sso_last_name: str
    staff_sso_email_address: str
    staff_sso_contact_email_address: str
    people_finder_image: str
    people_finder_first_name: str
    people_finder_last_name: str
    people_finder_job_title: str
    people_finder_directorate: str
    people_finder_phone: str
    people_finder_grade: str
    service_now_department_id: str
    service_now_department_name: str
    service_now_directorate_id: str
    service_now_directorate_name: str


class ConsolidatedStaffDocument(TypedDict):
    staff_sso_activity_stream_id: str
    first_name: str
    last_name: str
    email_address: str
    contact_email_address: str
    photo: str
    contact_phone: str
    contact_address: str
    date_of_birth: str
    grade: str
    directorate: str
    department: str
    job_title: str
    staff_id: str
    manager: str


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
                    {"match": {"staff_sso_first_name": {"query": query, "boost": 5.0}}},
                    {"match": {"staff_sso_last_name": {"query": query, "boost": 5.0}}},
                    {
                        "match": {
                            "staff_sso_email_address": {"query": query, "boost": 10.0}
                        }
                    },
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


def consolidate_staff_documents(
    *, staff_documents: List[StaffDocument]
) -> List[ConsolidatedStaffDocument]:
    consolidated_staff_documents: List[ConsolidatedStaffDocument] = []
    for staff_document in staff_documents:
        consolidated_staff_document: ConsolidatedStaffDocument = {
            "staff_sso_activity_stream_id": staff_document[
                "staff_sso_activity_stream_id"
            ],
            "first_name": staff_document["staff_sso_first_name"]
            or staff_document["people_finder_first_name"]
            or "",
            "last_name": staff_document["staff_sso_last_name"]
            or staff_document["people_finder_last_name"]
            or "",
            "email_address": staff_document["staff_sso_email_address"] or "",
            "contact_email_address": staff_document["staff_sso_contact_email_address"]
            or "",
            "contact_phone": staff_document["people_finder_phone"] or "",
            "contact_address": "",
            "date_of_birth": date(2021, 11, 25).strftime("%d-%m-%Y"),
            "photo": staff_document["people_finder_image"] or "",
            "grade": staff_document["people_finder_grade"] or "",
            "directorate": staff_document["service_now_directorate_id"] or "",
            "department": staff_document["service_now_department_id"] or "",
            "job_title": staff_document["people_finder_job_title"] or "",
            "staff_id": "",
            "manager": "",
        }
        consolidated_staff_documents.append(consolidated_staff_document)
    return consolidated_staff_documents
