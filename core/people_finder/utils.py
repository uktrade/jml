import logging
from typing import Optional

from opensearchpy.exceptions import NotFoundError

from core.people_finder import get_people_finder_interface
from core.people_finder.interfaces import PersonDetail
from core.utils.staff_index import update_staff_document

logger = logging.getLogger(__name__)


def index_people_finder_result(people_finder_result: PersonDetail) -> None:
    sso_user_id = people_finder_result.sso_user_id

    if not sso_user_id:
        return

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

    update_staff_document(id=sso_user_id, staff_document=mapped_data)


def ingest_people_finder(limit: Optional[int] = None) -> None:
    """Ingests staff data from the People Finder API.

    Args:
        limit: The max number of records to process.
    """
    people_finder = get_people_finder_interface()
    people_finder_results = people_finder.get_all()

    count = 0

    for people_finder_result in people_finder_results:
        if limit and count >= limit:
            break

        try:
            index_people_finder_result(people_finder_result=people_finder_result)
        except NotFoundError:
            continue
        except Exception:
            logger.exception(
                "An error occured whilst indexing %s", people_finder_result.sso_user_id
            )
        finally:
            count += 1
