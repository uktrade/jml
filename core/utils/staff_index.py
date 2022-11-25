import logging
import uuid
from dataclasses import dataclass
from functools import partial, wraps
from typing import Any, Dict, Iterable, List, Mapping, Optional, TypedDict

from dataclasses_json import DataClassJsonMixin
from django.conf import settings
from django.contrib.postgres.aggregates import ArrayAgg
from opensearch_dsl import Search
from opensearch_dsl.response import Hit
from opensearchpy import OpenSearch
from opensearchpy.exceptions import NotFoundError

from activity_stream.models import ActivityStreamStaffSSOUser

logger = logging.getLogger(__name__)


MAX_RESULTS = 100
MIN_SCORE = 0.02

HOST_URLS: List[str] = settings.SEARCH_HOST_URLS
STAFF_INDEX_NAME: str = settings.SEARCH_STAFF_INDEX_NAME
STAFF_INDEX_BODY: Mapping[str, Any] = {
    "mappings": {
        "properties": {
            "uuid": {"type": "text"},
            "available_in_staff_sso": {"type": "boolean"},
            "staff_sso_activity_stream_id": {"type": "text"},
            "staff_sso_email_user_id": {"type": "text"},
            "staff_sso_legacy_id": {"type": "text"},
            "staff_sso_first_name": {"type": "text"},
            "staff_sso_last_name": {"type": "text"},
            "staff_sso_contact_email_address": {"type": "text"},
            "staff_sso_email_addresses": {"type": "text"},  # Can accept list
            "people_finder_first_name": {"type": "text"},
            "people_finder_last_name": {"type": "text"},
            "people_finder_job_title": {"type": "text"},
            "people_finder_directorate": {"type": "text"},
            "people_finder_phone": {"type": "text"},
            "people_finder_grade": {"type": "text"},
            "people_finder_email": {"type": "text"},
            "people_finder_photo": {"type": "text"},
            "people_finder_photo_small": {"type": "text"},
        },
    },
}


@dataclass
class StaffDocument(DataClassJsonMixin):
    uuid: str
    available_in_staff_sso: bool
    staff_sso_activity_stream_id: str
    staff_sso_email_user_id: str
    staff_sso_legacy_id: str
    staff_sso_first_name: str
    staff_sso_last_name: str
    staff_sso_contact_email_address: str
    staff_sso_email_addresses: List[str]
    people_finder_first_name: str
    people_finder_last_name: str
    people_finder_job_title: str
    people_finder_directorate: str
    people_finder_phone: str
    people_finder_grade: str
    people_finder_email: str
    people_finder_photo: Optional[str]
    people_finder_photo_small: Optional[str]


class ConsolidatedStaffDocument(TypedDict):
    uuid: str
    available_in_staff_sso: bool
    staff_sso_activity_stream_id: str
    staff_sso_email_user_id: str
    first_name: str
    last_name: str
    contact_email_address: str
    email_addresses: List
    contact_phone: str
    grade: str
    department_name: str
    job_title: str
    manager: str
    photo: str
    photo_small: str


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


def search_staff_index(
    *,
    query: str,
    exclude_staff_ids: Optional[List[str]] = None,
    present_in_sso: bool = True,
) -> List[StaffDocument]:
    """
    Search the Staff index.

    query: The search query.
    exclude_staff_ids: A list of staff IDs to exclude from the results.
    present_in_sso: Whether to only return results that are present in Staff SSO.
    """
    if not exclude_staff_ids:
        exclude_staff_ids = []

    search_client = get_search_connection()
    search_dict = {
        "query": {
            "bool": {
                "filter": {
                    "term": {
                        "available_in_staff_sso": present_in_sso,
                    },
                },
                "should": [
                    {"match": {"staff_sso_first_name": {"query": query, "boost": 5.0}}},
                    {"match": {"staff_sso_last_name": {"query": query, "boost": 5.0}}},
                    {
                        "match": {
                            "staff_sso_email_addresses": {
                                "query": query,
                                "boost": 10.0,
                            }
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
            staff_documents.append(
                StaffDocument.from_dict(hit.to_dict(), infer_missing=True)
            )

    return staff_documents


class TooManyStaffDocumentsFound(Exception):
    pass


class StaffDocumentNotFound(Exception):
    pass


def get_staff_document_from_staff_index(
    *,
    sso_email_user_id: Optional[str] = None,
    staff_uuid: Optional[str] = None,
    sso_email_address: Optional[str] = None,
) -> StaffDocument:
    """
    Get a Staff document from the Staff index.
    """
    values = []
    if sso_email_user_id:
        values.append(sso_email_user_id)
    if staff_uuid:
        values.append(staff_uuid)
    if sso_email_address:
        values.append(sso_email_address)

    if len(values) != 1:
        raise ValueError(
            "One of staff_id, staff_uuid or sso_email_address must be provided, "
            "not multiple/all."
        )

    search_dict = {}
    if sso_email_user_id:
        search_dict = {
            "query": {
                "match_phrase": {
                    "staff_sso_email_user_id": {
                        "query": sso_email_user_id,
                    },
                }
            }
        }
    elif staff_uuid:
        search_dict = {
            "query": {
                "match_phrase": {
                    "uuid": {
                        "query": staff_uuid,
                    },
                }
            }
        }
    elif sso_email_address:
        search_dict = {
            "query": {
                "match_phrase": {
                    "staff_sso_email_addresses": {
                        "query": sso_email_address,
                    },
                }
            }
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
    if len(search_results) > 1:
        raise TooManyStaffDocumentsFound()

    hit: Hit = search_results.hits[0]

    return StaffDocument.from_dict(hit.to_dict(), infer_missing=True)


def consolidate_staff_documents(
    *, staff_documents: List[StaffDocument]
) -> List[ConsolidatedStaffDocument]:
    consolidated_staff_documents: List[ConsolidatedStaffDocument] = []
    for staff_document in staff_documents:
        consolidated_staff_document: ConsolidatedStaffDocument = {
            "uuid": staff_document.uuid,
            "available_in_staff_sso": staff_document.available_in_staff_sso,
            "staff_sso_email_user_id": staff_document.staff_sso_email_user_id,
            "staff_sso_activity_stream_id": staff_document.staff_sso_activity_stream_id,
            "first_name": staff_document.staff_sso_first_name
            or staff_document.people_finder_first_name
            or "",
            "last_name": staff_document.staff_sso_last_name
            or staff_document.people_finder_last_name
            or "",
            "contact_email_address": staff_document.staff_sso_contact_email_address
            or "",
            "email_addresses": staff_document.staff_sso_email_addresses or [],
            "contact_phone": staff_document.people_finder_phone or "",
            "grade": staff_document.people_finder_grade or "",
            # For the time being the department is hardcoded.
            "department_name": settings.SERVICE_NOW_DIT_DEPARTMENT_SYS_ID,
            "job_title": staff_document.people_finder_job_title or "",
            "photo": staff_document.people_finder_photo or "",
            "photo_small": staff_document.people_finder_photo_small or "",
            "manager": "",
        }
        consolidated_staff_documents.append(consolidated_staff_document)
    return consolidated_staff_documents


def get_people_finder_data(
    *, staff_sso_user: ActivityStreamStaffSSOUser
) -> Dict[str, str]:
    from core.people_finder import get_people_finder_interface
    from core.people_finder.interfaces import PeopleFinderPersonNotFound, PersonDetail

    people_finder = get_people_finder_interface()
    people_finder_data: Dict[str, str] = {
        "people_finder_email": "",
        "people_finder_first_name": "",
        "people_finder_last_name": "",
        "people_finder_job_title": "",
        "people_finder_directorate": "",
        "people_finder_phone": "",
        "people_finder_grade": "",
        "people_finder_photo": "",
        "people_finder_photo_small": "",
    }
    people_finder_result: Optional[PersonDetail] = None
    try:
        people_finder_result = people_finder.get_details(
            sso_legacy_user_id=staff_sso_user.user_id,
        )
    except PeopleFinderPersonNotFound:
        logger.exception(
            f"Could not find '{staff_sso_user}' in People Finder", exc_info=True
        )

    if people_finder_result:
        people_finder_data["people_finder_email"] = people_finder_result.email
        people_finder_data["people_finder_first_name"] = people_finder_result.first_name
        people_finder_data["people_finder_last_name"] = people_finder_result.last_name
        people_finder_data["people_finder_job_title"] = people_finder_result.job_title
        people_finder_data[
            "people_finder_directorate"
        ] = people_finder_result.directorate
        if people_finder_result.phone:
            people_finder_data["people_finder_phone"] = people_finder_result.phone
        if people_finder_result.grade:
            people_finder_data["people_finder_grade"] = people_finder_result.grade
        if people_finder_result.photo:
            people_finder_data["people_finder_photo"] = people_finder_result.photo
        if people_finder_result.photo_small:
            people_finder_data[
                "people_finder_photo_small"
            ] = people_finder_result.photo_small

    return people_finder_data


def get_service_now_data(
    *, staff_sso_user: ActivityStreamStaffSSOUser
) -> Dict[str, str]:
    from core.service_now import get_service_now_interface
    from core.service_now.interfaces import ServiceNowUserNotFound

    service_now_interface = get_service_now_interface()

    service_now_data = {
        "service_now_user_id": "",
        "service_now_department_id": "",
        "service_now_department_name": "",
    }

    # Iterate through all emails and check for Service Now record
    for sso_email_record in staff_sso_user.sso_emails.all():
        try:
            service_now_user = service_now_interface.get_user(
                email=sso_email_record.email_address,
            )
        except ServiceNowUserNotFound:
            continue
        else:
            service_now_user_id = service_now_user["sys_id"]
            service_now_data["service_now_user_id"] = service_now_user_id
            logger.info(f"Service Now id found: {service_now_user_id}")

            staff_sso_user.service_now_user_id = service_now_user_id
            staff_sso_user.service_now_email_address = sso_email_record.email_address
            staff_sso_user.save()

            break

    # Get Service Now Department data
    service_now_data[
        "service_now_department_id"
    ] = settings.SERVICE_NOW_DIT_DEPARTMENT_SYS_ID
    service_now_departments = service_now_interface.get_departments(
        sys_id=service_now_data["service_now_department_id"],
    )
    if len(service_now_departments) == 1:
        service_now_data["service_now_department_name"] = service_now_departments[0][
            "name"
        ]

    return service_now_data


def build_staff_document(*, staff_sso_user: ActivityStreamStaffSSOUser):
    staff_sso_data = {
        "available_in_staff_sso": staff_sso_user.available,
        "staff_sso_legacy_id": staff_sso_user.user_id,
        "staff_sso_email_user_id": staff_sso_user.email_user_id,
        "staff_sso_activity_stream_id": staff_sso_user.identifier,
        "staff_sso_first_name": staff_sso_user.first_name,
        "staff_sso_last_name": staff_sso_user.last_name,
        "staff_sso_email_addresses": list(
            staff_sso_user.sso_emails.values_list("email_address", flat=True)
        ),
        "staff_sso_contact_email_address": staff_sso_user.contact_email_address or "",
    }

    staff_document_dict: Dict[str, Any] = {
        # Staff SSO
        **staff_sso_data,
        # People Finder
        **get_people_finder_data(staff_sso_user=staff_sso_user),
        # Service Now
        **get_service_now_data(staff_sso_user=staff_sso_user),
    }

    return StaffDocument.from_dict(staff_document_dict, infer_missing=True)


def get_csd_for_activitystream_user(
    *, activitystream_user: Optional[ActivityStreamStaffSSOUser]
) -> Optional[ConsolidatedStaffDocument]:
    if not activitystream_user:
        return None

    sso_email_user_id = activitystream_user.email_user_id
    staff_document = get_staff_document_from_staff_index(
        sso_email_user_id=sso_email_user_id,
    )
    if not staff_document:
        return None

    consolidated_staff_documents = consolidate_staff_documents(
        staff_documents=[staff_document],
    )
    return consolidated_staff_documents[0]


def get_staff_document(id: str) -> dict[str, Any]:
    search_client = get_search_connection()
    return search_client.get(index=STAFF_INDEX_NAME, id=id)


def delete_staff_document(id: str) -> None:
    search_client = get_search_connection()
    search_client.delete(index=STAFF_INDEX_NAME, id=id)


def update_staff_document(
    id: str, staff_document: dict[str, Any], upsert: bool = False
) -> None:
    """Update the related staff document in the staff search index."""
    search_client = get_search_connection()

    if "uuid" not in staff_document or not staff_document["uuid"]:
        staff_document["uuid"] = str(uuid.uuid4())

    body = {"doc": staff_document}

    if upsert:
        body |= {"upsert": staff_document}

    # https://opensearch.org/docs/latest/opensearch/index-data/#update-data
    search_client.update(
        index=STAFF_INDEX_NAME,
        body=body,
        id=id,
    )


def staff_document_updater(func, upsert=False):
    @wraps(func)
    def wrapper(*args, **kwargs):
        for doc_id, doc in func(*args, **kwargs):
            update_staff_document(doc_id, doc, upsert=upsert)

    return wrapper


@partial(staff_document_updater, upsert=True)
def index_sso_users():
    qs = (
        ActivityStreamStaffSSOUser.objects.annotate(
            emails=ArrayAgg("sso_emails__email_address", distinct=True)
        )
        .all()
        .iterator()
    )

    for sso_user in qs:
        doc_id = sso_user.email_user_id
        doc = {
            "available_in_staff_sso": sso_user.available,
            "staff_sso_activity_stream_id": sso_user.identifier,
            "staff_sso_email_user_id": sso_user.email_user_id,
            "staff_sso_legacy_id": sso_user.user_id,
            "staff_sso_first_name": sso_user.first_name,
            "staff_sso_last_name": sso_user.last_name,
            "staff_sso_contact_email_address": sso_user.contact_email_address or "",
            # `emails` come from the annotate in the queryset.
            "staff_sso_email_addresses": sso_user.emails,
        }

        yield doc_id, doc


def get_all_staff_documents(self) -> Iterable[StaffDocument]:
    """
    Get all staff documents from the staff index.

    NOTE: This function will take a long time to run on production.
    """

    search_client = get_search_connection()
    search_dict: Dict = {"query": {"match_all": {}}}

    search = (
        Search(index=STAFF_INDEX_NAME)
        .using(search_client)
        .update_from_dict(search_dict)
    )
    search_results = search.execute()

    total_document_count = search_results.hits.total.value
    page_size = 100
    indexed_count = 0

    while indexed_count < total_document_count:
        paginated_search = search.extra(from_=indexed_count, size=page_size)
        paginated_search_results = paginated_search.execute()
        for hit in paginated_search_results:
            yield StaffDocument.from_dict(hit.to_dict(), infer_missing=True)
        indexed_count += page_size


def update_all_staff_documents_with_a_uuid():
    """
    Make sure all staff documents have a UUID value.

    NOTE: This function will take a long time to run on production.
    """

    for staff_document in get_all_staff_documents():
        if staff_document.uuid:
            continue
        if not staff_document.staff_sso_email_user_id:
            continue

        # Calling update_staff_document with a document that has no uuid,
        # will have one generated.
        update_staff_document(
            staff_document.staff_sso_email_user_id,
            staff_document=staff_document.to_dict(),
            upsert=False,
        )
