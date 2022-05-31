from core.people_finder import get_people_finder_interface
from core.utils.staff_index import index_staff_document, search_staff_index


def ingest_people_finder():
    people_finder_search = get_people_finder_interface()

    people_finder_results = people_finder_search.get_search_results(search_term="")

    for people_finder_result in people_finder_results:
        staff_index_results = search_staff_index(query=people_finder_result["email"])
        if len(staff_index_results) == 0:
            continue
        staff_index_result = staff_index_results[0]

        staff_index_result.update(
            people_finder_image=people_finder_result.get("image", ""),
            people_finder_first_name=people_finder_result.get("first_name", ""),
            people_finder_last_name=people_finder_result.get("last_name", ""),
            people_finder_job_title=people_finder_result.get("job_title", ""),
            people_finder_directorate=people_finder_result.get("directorate", ""),
            people_finder_phone=people_finder_result.get("phone", ""),
            people_finder_grade=people_finder_result.get("grade", ""),
            people_finder_email=people_finder_result.get("email", ""),
        )

        index_staff_document(staff_document=staff_index_result)
