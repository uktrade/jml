"""
Make sure all staff indexed in opensearch have a uuid set.
"""

from typing import List

from django.core.management.base import BaseCommand
from opensearch_dsl import Search

from core.utils.staff_index import (
    STAFF_INDEX_NAME,
    StaffDocument,
    get_search_connection,
    update_staff_document,
)


class Command(BaseCommand):
    help = "Ingest Staff SSO Activity Stream"

    def handle(self, *args, **options) -> None:
        staff_documents_to_update = self.get_all_staff_documents()
        for staff_document in staff_documents_to_update:
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

    def get_all_staff_documents(self) -> List[StaffDocument]:
        search_client = get_search_connection()
        search_dict = {"query": {"match_all": {}}}

        search = (
            Search(index=STAFF_INDEX_NAME)
            .using(search_client)
            .update_from_dict(search_dict)
        )
        search_results = search.execute()

        return [
            StaffDocument.from_dict(hit.to_dict(), infer_missing=True)
            for hit in search_results.hits
        ]
