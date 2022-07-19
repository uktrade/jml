from core.people_finder import get_people_finder_interface
from core.people_finder.interfaces import PersonDetail
from core.utils.staff_index import (
    StaffDocument,
    StaffDocumentNotFound,
    TooManyStaffDocumentsFound,
    get_staff_document_from_staff_index,
    index_staff_document,
)


def index_people_finder_result(people_finder_result: PersonDetail) -> None:
    try:
        staff_index_result = get_staff_document_from_staff_index(
            sso_email_address=people_finder_result["email"]
        ).to_dict()
    except (StaffDocumentNotFound, TooManyStaffDocumentsFound):
        return None

    mapped_data = {
        "people_finder_photo": people_finder_result.photo,
        "people_finder_photo_small": people_finder_result.photo_small,
        "people_finder_first_name": people_finder_result.first_name,
        "people_finder_last_name": people_finder_result.last_name,
        "people_finder_job_title": people_finder_result.job_title,
        "people_finder_directorate": people_finder_result.directorate,
        "people_finder_phone": people_finder_result.phone,
        "people_finder_grade": people_finder_result.grade,
        "people_finder_email": people_finder_result.email,
    }

    # Only update values that have data.
    for key, value in mapped_data.items():
        if value:
            staff_index_result[key] = value

    index_staff_document(staff_document=StaffDocument.from_dict(staff_index_result))

    return None


def ingest_people_finder():
    people_finder = get_people_finder_interface()
    people_finder_results = people_finder.get_all()

    for people_finder_result in people_finder_results:
        try:
            index_people_finder_result(people_finder_result=people_finder_result)
        except Exception:
            continue
