from typing import Any, Dict, List

from django.http.response import HttpResponse
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from core.people_finder import get_people_finder_interface
from core.staff_search.forms import SearchForm
from core.utils.staff_index import (
    ConsolidatedStaffDocument,
    consolidate_staff_documents,
    search_staff_index,
)


class StaffSearchView(FormView):
    """
    Generic Staff Search View

    This view is used to search for staff members. Update the following values
    to customise the view text and behaviour:
    - success_url: The URL to redirect to after a successful search.
    - search_name: A more specific name for the type of staff you are searching for.
    - query_param_name: The name of the query parameter the staff ID will be passed on success.
    """

    form_class = SearchForm
    template_name = "staff_search/search.html"
    success_url = reverse_lazy("staff-search")
    query_param_name: str = "person_id"

    search_name: str = "member of staff"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.people_finder_search = get_people_finder_interface()
        self.exclude_staff_ids: List[str] = []

    def process_search(self, search_terms) -> List[ConsolidatedStaffDocument]:
        return consolidate_staff_documents(
            staff_documents=search_staff_index(
                query=search_terms,
                exclude_staff_ids=self.exclude_staff_ids,
            ),
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            search_term="",
            staff_results=[],
            success_url=self.success_url,
            search_name=self.search_name,
            query_param_name=self.query_param_name,
        )
        return context

    def form_valid(self, form) -> HttpResponse:
        context = self.get_context_data()

        search_terms = form.cleaned_data["search_terms"]
        staff_results = self.process_search(search_terms)

        context.update(
            search_term=search_terms,
            staff_results=staff_results,
        )
        return self.render_to_response(context)
