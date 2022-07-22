import logging
import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, List, Mapping, Optional, TypedDict

from dataclasses_json import DataClassJsonMixin
from django.conf import settings
from opensearch_dsl import Search
from opensearch_dsl.response import Hit
from opensearchpy import OpenSearch
from opensearchpy.exceptions import NotFoundError

from activity_stream.models import ActivityStreamStaffSSOUser, ServiceEmailAddress
from core.people_finder.client import FailedToGetPersonRecord

logger = logging.getLogger(__name__)


MAX_RESULTS = 100
MIN_SCORE = 0.02

HOST_URLS: List[str] = settings.SEARCH_HOST_URLS
STAFF_INDEX_NAME: str = settings.SEARCH_STAFF_INDEX_NAME
STAFF_INDEX_BODY: Mapping[str, Any] = {
    "mappings": {
        "properties": {
            "uuid": {"type": "text"},
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
            "people_finder_photo": {"type": "text"},
            "people_finder_photo_small": {"type": "text"},
            "service_now_user_id": {"type": "text"},
            "service_now_department_id": {"type": "text"},
            "service_now_department_name": {"type": "text"},
            "people_data_employee_number": {"type": "text"},
            "people_data_uksbs_person_id": {"type": "text"},
        },
    },
}


@dataclass
class StaffDocument(DataClassJsonMixin):
    uuid: str
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
    service_now_user_id: str
    service_now_department_id: str
    service_now_department_name: str
    people_data_employee_number: Optional[str]
    people_data_uksbs_person_id: Optional[str]


class ConsolidatedStaffDocument(TypedDict):
    uuid: str
    staff_sso_activity_stream_id: str
    staff_sso_email_user_id: str
    first_name: str
    last_name: str
    contact_email_address: str
    email_addresses: List
    contact_phone: str
    grade: str
    department: str
    department_name: str
    job_title: str
    staff_id: str
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


def index_staff_document(*, staff_document: StaffDocument):
    """
    Delete existing StaffDocument and create a new one in the Staff index.
    """
    search_client = get_search_connection()
    existing_document: Optional[StaffDocument] = None
    if staff_document.staff_sso_email_user_id:
        try:
            existing_document = get_staff_document_from_staff_index(
                sso_email_user_id=staff_document.staff_sso_email_user_id
            )
        except StaffDocumentNotFound:
            pass

    if existing_document:
        search_client.delete_by_query(
            index=STAFF_INDEX_NAME,
            body={
                "query": {
                    "match_phrase": {
                        "staff_sso_email_user_id": existing_document.staff_sso_email_user_id
                    }
                }
            },
            ignore=400,
        )

    search_client.index(
        index=STAFF_INDEX_NAME,
        body=staff_document.to_dict(),
    )


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
            # TODO: Drop infer_missing=True once we have plugged into all live data
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

    # TODO: Drop infer_missing=True once we have plugged into all live data
    return StaffDocument.from_dict(hit.to_dict(), infer_missing=True)


def consolidate_staff_documents(
    *, staff_documents: List[StaffDocument]
) -> List[ConsolidatedStaffDocument]:
    consolidated_staff_documents: List[ConsolidatedStaffDocument] = []
    for staff_document in staff_documents:
        consolidated_staff_document: ConsolidatedStaffDocument = {
            "uuid": staff_document.uuid,
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
            "department": staff_document.service_now_department_id or "",
            "department_name": staff_document.service_now_department_name or "",
            "job_title": staff_document.people_finder_job_title or "",
            "staff_id": staff_document.people_data_employee_number or "",
            "person_id": staff_document.people_data_uksbs_person_id or "",
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
            ServiceEmailAddress.objects.update_or_create(
                staff_sso_user=staff_sso_user,
                service_now_email_address=sso_email_record.email_address,
            )
            service_now_user_id = service_now_user["sys_id"]
            service_now_data["service_now_user_id"] = service_now_user_id
            logger.info(f"Service Now id found: {service_now_user_id}")
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

    """
    Get People report data
    """
    from core.people_data import get_people_data_interface

    people_data_search = get_people_data_interface()
    people_data_results = people_data_search.get_people_data(
        sso_legacy_id=staff_sso_user.user_id,
    )
    # Assuming first id is correct
    employee_number = next(iter(people_data_results["employee_numbers"]), None)

    """
    Build Staff Document
    """
    staff_document_dict: Dict[str, Any] = {
        "uuid": str(uuid.uuid4()),
        # Staff SSO
        **staff_sso_data,
        # People Finder
        **get_people_finder_data(staff_sso_user=staff_sso_user),
        # Service Now
        **get_service_now_data(staff_sso_user=staff_sso_user),
        # People Data
        "people_data_employee_number": employee_number,
        "people_data_uksbs_person_id": people_data_results["uksbs_person_id"],
    }
    return StaffDocument.from_dict(staff_document_dict)


def index_staff_by_emails(emails: List[str]) -> None:
    for staff_sso_user in ActivityStreamStaffSSOUser.objects.filter(
        sso_emails__email_address__in=emails,
    ):
        try:
            staff_document = build_staff_document(staff_sso_user=staff_sso_user)
            index_staff_document(staff_document=staff_document)
        except FailedToGetPersonRecord:
            logger.error(
                f"No People Finder record could be accessed for '{staff_sso_user}'"
            )
        except Exception:
            logger.exception(
                f"Could not build index entry for '{staff_sso_user}''", exc_info=True
            )


def index_all_staff() -> int:
    """
    Index all staff to the Staff Search Index

    POTENTIALLY LONG RUNNING TASK

    Things to consider:
    - API rate limits/throttling?
    - Using asyncronous tasks
    """
    indexed_count = 0
    current_date = date.today()
    days_ago = 6 * 30
    last_accessed_datetime = current_date - timedelta(days=days_ago)
    # Add documents to the index
    for staff_sso_user in ActivityStreamStaffSSOUser.objects.filter(
        became_inactive_on__isnull=True,
        last_accessed__isnull=False,
        last_accessed__gte=last_accessed_datetime,
    ):
        try:
            staff_document = build_staff_document(staff_sso_user=staff_sso_user)
            index_staff_document(staff_document=staff_document)
            indexed_count += 1
        except FailedToGetPersonRecord:
            logger.error(
                f"No People Finder record could be accessed for '{staff_sso_user}'"
            )
        except Exception:
            logger.exception(
                f"Could not build index entry for '{staff_sso_user}''", exc_info=True
            )

    return indexed_count
