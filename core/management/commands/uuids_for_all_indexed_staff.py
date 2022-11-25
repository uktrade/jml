"""
Make sure all staff indexed in opensearch have a uuid set.
"""

from typing import Dict, Iterable

from django.core.management.base import BaseCommand
from opensearch_dsl import Search

from core.utils.staff_index import (
    STAFF_INDEX_NAME,
    StaffDocument,
    get_search_connection,
    update_staff_document,
)


class Command(BaseCommand):
    help = "Update staff documents to make sure they all have UUIDs"

    def handle(self, *args, **options) -> None:
        for staff_document in self.get_all_staff_documents():
            print(staff_document)
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

    def get_all_staff_documents(self) -> Iterable[StaffDocument]:
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
