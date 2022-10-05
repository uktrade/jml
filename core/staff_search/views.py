from typing import Any, Dict, List
from uuid import UUID

from django.http import Http404
from django.http.response import HttpResponse
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from core.people_finder import get_people_finder_interface
from core.staff_search.forms import SearchForm
from core.utils.staff_index import (
    ConsolidatedStaffDocument,
    consolidate_staff_documents,
    get_staff_document_from_staff_index,
    search_staff_index,
)


class StaffResultView(TemplateView):
    template_name = "staff_search/staff_result.html"

    def dispatch(self, request, *args, **kwargs):
        self.staff_uuid: UUID = kwargs["staff_uuid"]

        staff_document = get_staff_document_from_staff_index(staff_uuid=self.staff_uuid)
        if not staff_document:
            raise Http404

        self.consolidated_staff_document = consolidate_staff_documents(
            staff_documents=[staff_document]
        )[0]

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(staff_details=self.consolidated_staff_document)
        return context


class StaffSearchView(FormView):
    """
    Generic Staff Search View

    This view is used to search for staff members. Update the following values
    to customise the view text and behaviour:
    - search_name: A more specific name for the type of staff you are searching for.
    - query_param_name: The name of the query parameter the staff ID will be passed on success.
    """

    form_class = SearchForm
    template_name = "staff_search/search.html"
    search_name: str = "member of staff"
    query_param_name: str = "staff_uuid"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.people_finder_search = get_people_finder_interface()
        self.exclude_staff_ids: List[str] = []

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()

        form_kwargs["data"] = dict(form_kwargs["data"])

        search_terms = ""
        search_term_keys: List[str] = []

        for key, value in form_kwargs["data"].items():
            if "search_terms" in key:
                search_terms = value
            search_term_keys.append(key)

        for search_term_key in search_term_keys:
            del form_kwargs["data"][search_term_key]

        form_kwargs["data"]["search_terms"] = search_terms

        return form_kwargs

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
