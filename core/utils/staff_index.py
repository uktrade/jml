import uuid
from typing import Any, Dict, List, Mapping, Optional, TypedDict, Union, cast

from django.conf import settings
from opensearch_dsl import Search
from opensearchpy import OpenSearch
from opensearchpy.exceptions import NotFoundError

from activity_stream.models import ActivityStreamStaffSSOUser
from core.people_finder.interfaces import PersonDetail

MAX_RESULTS = 100
MIN_SCORE = 0.02

HOST_URLS: List[str] = settings.SEARCH_HOST_URLS
STAFF_INDEX_NAME: str = settings.SEARCH_STAFF_INDEX_NAME
STAFF_INDEX_BODY: Mapping[str, Any] = {
    "mappings": {
        "properties": {
            "uuid": {"type": "text"},
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
            "service_now_user_id": {"type": "text"},
            "service_now_department_id": {"type": "text"},
            "service_now_department_name": {"type": "text"},
            "service_now_directorate_id": {"type": "text"},
            "service_now_directorate_name": {"type": "text"},
            "people_data_staff_ids": {"type": "text"}, # TODO Needs to use correct type
        },
    },
}


class StaffDocument(TypedDict):
    uuid: str
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
    people_finder_email: str
    service_now_user_id: str
    service_now_department_id: str
    service_now_department_name: str
    service_now_directorate_id: str
    service_now_directorate_name: str
    staff_ids: List[str]


class ConsolidatedStaffDocument(TypedDict):
    uuid: str
    staff_sso_activity_stream_id: str
    first_name: str
    last_name: str
    email_address: str
    contact_email_address: str
    photo: str
    contact_phone: str
    grade: str
    directorate: str
    directorate_name: str
    department: str
    department_name: str
    job_title: str
    staff_id: str
    manager: str
    oracle_id: str


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


def clear_staff_index():
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
    Add or Update a Staff document in the Staff index.
    """
    search_client = get_search_connection()
    if search_client.exists(index=STAFF_INDEX_NAME, id=staff_document["uuid"]):
        search_client.update(
            index=STAFF_INDEX_NAME,
            id=staff_document["uuid"],
            body=staff_document,
        )
    else:
        search_client.index(
            index=STAFF_INDEX_NAME,
            body=staff_document,
        )


def get_all_staff_documents() -> List[StaffDocument]:
    """
    Get all Staff documents from the Staff index.
    """
    return search_staff_index(query="")


def search_staff_index(
    *, query: str, exclude_staff_ids: Optional[List[str]] = None
) -> List[StaffDocument]:
    """
    Search the Staff index.
    """
    if not exclude_staff_ids:
        exclude_staff_ids = []

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
        if hit["staff_sso_activity_stream_id"] not in exclude_staff_ids:
            staff_document = cast(
                StaffDocument,
                {
                    field_name: hit[field_name]
                    for field_name in StaffDocument.__annotations__
                },
            )
            staff_documents.append(staff_document)

    return staff_documents


class StaffDocumentNotFound(Exception):
    pass


def get_staff_document_from_staff_index(
    *, staff_id: Optional[str] = None, staff_uuid: Optional[str] = None
) -> StaffDocument:
    """
    Get a Staff document from the Staff index.
    """
    if not staff_id and not staff_uuid or staff_id and staff_uuid:
        raise ValueError("One of staff_id or staff_uuid must be provided, not both")

    search_field: str = ""
    search_value: str = ""
    if staff_id:
        search_field = "staff_sso_activity_stream_id"
        search_value = staff_id
    elif staff_uuid:
        search_field = "uuid"
        search_value = staff_uuid

    search_dict = {
        "query": {
            "bool": {
                "should": [
                    {"match": {search_field: {"query": search_value}}},
                ],
                "minimum_should_match": 1,
                "boost": 1.0,
            },
        },
        "sort": {
            "_score": {"order": "desc"},
        },
        "size": MAX_RESULTS,
        "min_score": MIN_SCORE,
    }

    search_client = get_search_connection()

    search = (
        Search(index=STAFF_INDEX_NAME)
        .using(search_client)
        .update_from_dict(search_dict)
    )
    search_results = search.execute()

    if len(search_results) == 0:
        raise StaffDocumentNotFound()

    staff_document = cast(
        StaffDocument,
        {
            field_name: search_results.hits[0][field_name]
            for field_name in StaffDocument.__annotations__
        },
    )
    return staff_document


def consolidate_staff_documents(
    *, staff_documents: List[StaffDocument]
) -> List[ConsolidatedStaffDocument]:
    consolidated_staff_documents: List[ConsolidatedStaffDocument] = []
    for staff_document in staff_documents:
        consolidated_staff_document: ConsolidatedStaffDocument = {
            "uuid": staff_document["uuid"],
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
            "photo": staff_document["people_finder_image"] or "",
            "grade": staff_document["people_finder_grade"] or "",
            "directorate": staff_document["service_now_directorate_id"] or "",
            "directorate_name": staff_document["service_now_directorate_name"] or "",
            "department": staff_document["service_now_department_id"] or "",
            "department_name": staff_document["service_now_department_name"] or "",
            "job_title": staff_document["people_finder_job_title"] or "",
            "staff_ids": staff_document["people_data_staff_ids"] or [],
            "manager": "",
        }
        consolidated_staff_documents.append(consolidated_staff_document)
    return consolidated_staff_documents


def build_staff_document(*, staff_sso_user: ActivityStreamStaffSSOUser):
    from core.people_data.interfaces import get_people_data_interface
    from core.people_finder import get_people_finder_interface
    from core.service_now import get_service_now_interface
    from core.service_now.interfaces import ServiceNowUserNotFound

    people_data_search = get_people_data_interface()
    people_finder_search = get_people_finder_interface()
    service_now_interface = get_service_now_interface()

    """
    Get People Finder data
    """
    people_finder_results = people_finder_search.get_search_results(
        search_term=staff_sso_user.email_address,
    )
    people_finder_result: Union[Dict, PersonDetail] = {}
    if len(people_finder_results) > 0:
        for pf_result in people_finder_results:
            if pf_result["email"] == staff_sso_user.email_address:
                people_finder_result = pf_result
    people_finder_directorate: Optional[str] = people_finder_result.get("directorate")

    """
    Get People report data
    """
    people_data_results = people_data_search.get_people_data(
        sso_legacy_id=staff_sso_user.user_id,
    )
    # TODO - add people data to index

    """
    Get Service Now data
    """
    # Get Service Now User data
    service_now_user_id: str = ""
    try:
        service_now_user = service_now_interface.get_user(
            email=staff_sso_user.email_address,
        )
    except ServiceNowUserNotFound:
        pass
    else:
        service_now_user_id = service_now_user["sys_id"]
    # Get Service Now Department data
    service_now_department_id: str = settings.SERVICE_NOW_DIT_DEPARTMENT_SYS_ID
    service_now_department_name: str = ""
    service_now_departments = service_now_interface.get_departments(
        sys_id=service_now_department_id,
    )
    if len(service_now_departments) == 1:
        service_now_department_name = service_now_departments[0]["name"]
    # Get Service Now Directorate data
    service_now_directorate_id: str = ""
    service_now_directorate_name: str = ""
    if people_finder_directorate:
        service_now_directorates = service_now_interface.get_directorates(
            name=people_finder_directorate,
        )
        if len(service_now_directorates) == 1:
            service_now_directorate_id = service_now_directorates[0]["sys_id"]
            service_now_directorate_name = service_now_directorates[0]["name"]

    """
    Build Staff Document
    """
    staff_document: StaffDocument = {
        "uuid": str(uuid.uuid4()),
        # Staff SSO
        "staff_sso_activity_stream_id": staff_sso_user.identifier,
        "staff_sso_first_name": staff_sso_user.first_name,
        "staff_sso_last_name": staff_sso_user.last_name,
        "staff_sso_email_address": staff_sso_user.email_address,
        "staff_sso_contact_email_address": staff_sso_user.contact_email_address or "",
        # People Finder
        "people_finder_image": people_finder_result.get("image", ""),
        "people_finder_first_name": people_finder_result.get("first_name", ""),
        "people_finder_last_name": people_finder_result.get("last_name", ""),
        "people_finder_job_title": people_finder_result.get("job_title", ""),
        "people_finder_directorate": people_finder_result.get("directorate", ""),
        "people_finder_phone": people_finder_result.get("phone", ""),
        "people_finder_grade": people_finder_result.get("grade", ""),
        "people_finder_email": people_finder_result.get("email", ""),
        # Service Now
        "service_now_user_id": service_now_user_id,
        "service_now_department_id": service_now_department_id,
        "service_now_department_name": service_now_department_name,
        "service_now_directorate_id": service_now_directorate_id,
        "service_now_directorate_name": service_now_directorate_name,
    }
    return staff_document


def index_all_staff() -> int:
    """
    Index all staff to the Staff Search Index

    POTENTIALLY LONG RUNNING TASK

    Things to consider:
    - API rate limits/throttling?
    - Using asyncronous tasks
    """
    staff_documents: List[StaffDocument] = []
    # Add documents to the index
    for staff_sso_user in ActivityStreamStaffSSOUser.objects.all():
        staff_document = build_staff_document(staff_sso_user=staff_sso_user)
        staff_documents.append(staff_document)
    indexed_count = 0
    for staff_document in staff_documents:
        index_staff_document(staff_document=staff_document)
        indexed_count += 1

    return indexed_count
