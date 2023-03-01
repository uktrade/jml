import logging
import uuid
from dataclasses import dataclass
from functools import partial, wraps
from typing import Any, Dict, List, Mapping, Optional, TypedDict

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
    job_title: str
    manager: str
    photo: str
    photo_small: str


def get_search_connection() -> OpenSearch:
    """Get the OpenSearch connection.

    Raises:
        Exception: If the Elasticsearch hosts are not configured.

    Returns:
        OpenSearch: The OpenSearch connection.
    """
    if not HOST_URLS:
        raise Exception("Elasticsearch hosts not configured")
    return OpenSearch(HOST_URLS)


def create_staff_index():
    """Create the Staff index."""
    search_client = get_search_connection()
    search_client.indices.create(index=STAFF_INDEX_NAME, body=STAFF_INDEX_BODY)


def delete_staff_index():
    """Delete the entire index."""
    search_client = get_search_connection()
    search_client.indices.delete(index=STAFF_INDEX_NAME)


def clear_staff_index():
    """Delete all documents from the index."""
    search_client = get_search_connection()
    search_client.delete_by_query(
        index=STAFF_INDEX_NAME,
        body={"query": {"match_all": {}}},
        ignore=400,
    )


class StaffIndexNotFound(Exception):
    pass


def staff_index_mapping_changed() -> bool:
    """Check to see if the existing mapping and our expected mapping differ.

    Raises:
        StaffIndexNotFound: If the index does not exist.

    Returns:
        bool: True if the mapping has changed, False otherwise.
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
    """Search the Staff index.

    Args:
        query (str):
            The search query.
        exclude_staff_ids (Optional[List[str]], optional):
            A list of staff IDs to exclude from the results.
            Defaults to None.
        present_in_sso (bool, optional):
            Whether to only return results that are present in Staff SSO.
            Defaults to True.

    Returns:
        List[StaffDocument]
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
                    {
                        "match": {
                            "staff_sso_first_name": {
                                "query": query,
                                "boost": 5.0,
                            },
                        },
                    },
                    {
                        "match": {
                            "staff_sso_last_name": {
                                "query": query,
                                "boost": 5.0,
                                "fuzziness": 2,
                                "fuzzy_transpositions": True,
                            },
                        },
                    },
                    {
                        "match": {
                            "staff_sso_email_addresses": {
                                "query": query,
                                "boost": 10.0,
                            }
                        }
                    },
                    {
                        "multi_match": {
                            "query": query,
                            "analyzer": "standard",
                        },
                    },
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
    """Get a Staff document from the Staff index.

    Args:
        sso_email_user_id (Optional[str], optional):
            The email user id to search for. Defaults to None.
        staff_uuid (Optional[str], optional):
            The staff UUID to search for. Defaults to None.
        sso_email_address (Optional[str], optional):
            The SSO email address to search for. Defaults to None.

    Raises:
        ValueError:
            If more than one of sso_email_user_id, staff_uuid or sso_email_address are provided.
        StaffDocumentNotFound:
            If no StaffDocument is found.
        TooManyStaffDocumentsFound:
            If more than one StaffDocument is found.

    Returns:
        StaffDocument
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
    """Convert a list of StaffDocuments into ConsolidatedStaffDocuments.

    Args:
        staff_documents (List[StaffDocument]):
            The list of StaffDocuments to consolidate.

    Returns:
        List[ConsolidatedStaffDocument]:
            The list of ConsolidatedStaffDocuments.
    """
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
    """Get the people finder data for a staff user.

    Args:
        staff_sso_user (ActivityStreamStaffSSOUser): The staff user to get the data for.

    Returns:
        Dict[str, str]: The people finder data.
    """
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


def build_staff_document(
    *, staff_sso_user: ActivityStreamStaffSSOUser
) -> StaffDocument:
    """Builds a StaffDocument from a StaffSSOUser.

    Args:
        staff_sso_user (ActivityStreamStaffSSOUser):
            The StaffSSOUser to build the StaffDocument from.

    Returns:
        StaffDocument:
            The StaffDocument built from the StaffSSOUser.
    """
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
    }

    return StaffDocument.from_dict(staff_document_dict, infer_missing=True)


def get_csd_for_activitystream_user(
    *, activitystream_user: Optional[ActivityStreamStaffSSOUser]
) -> Optional[ConsolidatedStaffDocument]:
    """Get the consolidated staff document for the given activity stream user.

    Args:
        activitystream_user (Optional[ActivityStreamStaffSSOUser]): The activity stream user.

    Returns:
        Optional[ConsolidatedStaffDocument]: The consolidated staff document.
    """
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


def get_sso_user_by_staff_document_uuid(uuid: str) -> ActivityStreamStaffSSOUser:
    """Get the staff SSO user from the staff index using it's UUID.

    Args:
        uuid (str): The Staff's UUID.

    Returns:
        ActivityStreamStaffSSOUser: The staff SSO user.
    """
    staff_doc = get_staff_document_from_staff_index(staff_uuid=uuid)

    return ActivityStreamStaffSSOUser.objects.get(
        email_user_id=staff_doc.staff_sso_email_user_id
    )


def delete_staff_document(id: str) -> None:
    """Delete the related staff document in the staff search index."""
    search_client = get_search_connection()
    search_client.delete(index=STAFF_INDEX_NAME, id=id)


def update_staff_document(
    id: str, staff_document: dict[str, Any], upsert: bool = False
) -> None:
    """Update the related staff document in the staff search index."""
    search_client = get_search_connection()

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
    """Decorator to update the staff document in the staff search index.

    Args:
        func (Callable):
            The function to decorate.
        upsert (bool, optional):
            Whether to upsert the document if it doesn't exist. Defaults to False.

    Returns:
        func (Callable): The decorated function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        for doc_id, doc in func(*args, **kwargs):
            update_staff_document(doc_id, doc, upsert=upsert)

    return wrapper


@partial(staff_document_updater, upsert=True)
def index_sso_users():
    """Index all SSO users in the staff search index.

    Yields:
        document_to_index (Tuple[str, dict[str, Any]]): The document ID and document to be indexed.
    """
    qs = (
        ActivityStreamStaffSSOUser.objects.annotate(
            emails=ArrayAgg("sso_emails__email_address", distinct=True)
        )
        .all()
        .iterator()
    )

    for sso_user in qs:
        doc_id = sso_user.email_user_id
        doc: Dict[str, Any] = {
            "uuid": str(uuid.uuid4()),
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
