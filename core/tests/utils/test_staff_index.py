from typing import Any
from unittest import skip

import pytest
from opensearchpy.exceptions import NotFoundError

from core.utils.staff_index import (
    STAFF_INDEX_NAME,
    delete_staff_document,
    get_search_connection,
    update_staff_document,
)


def get_staff_document(id: str) -> dict[str, Any]:
    search_client = get_search_connection()
    return search_client.get(index=STAFF_INDEX_NAME, id=id)


@skip("We don't run opensearch in CI")
def test_scenario_staff_document():
    id = "test.id.please.ignore-1234abcd@example.com"  # /PS-IGNORE
    staff_doc = {
        "first_name": "Test",
        "last_name": "Doc",
    }

    try:
        delete_staff_document(id=id)
    except NotFoundError:
        pass

    # given no doc
    # when we try to get it
    # then we get an error
    with pytest.raises(NotFoundError):
        get_staff_document(id=id)

    # given no doc
    # when we try to add one without upsert
    # then we get an error
    with pytest.raises(NotFoundError):
        update_staff_document(id=id, staff_document=staff_doc)

    # given a doc
    update_staff_document(id=id, staff_document=staff_doc, upsert=True)
    # when we try to get it
    doc = get_staff_document(id=id)
    # then we get the doc
    assert doc["_id"] == id
    assert doc["_source"] == staff_doc

    # given a doc
    # when we try to extend it
    update_staff_document(id=id, staff_document={"age": 42})
    # then we get the extended doc
    doc = get_staff_document(id=id)
    assert doc["_source"] == staff_doc | {"age": 42}

    # given a doc
    # when we try to extend it with upsert
    update_staff_document(id=id, staff_document={"hair_colour": "blonde"}, upsert=True)
    # then we get the extended doc
    doc = get_staff_document(id=id)
    assert doc["_source"] == staff_doc | {"age": 42} | {"hair_colour": "blonde"}

    # given a doc
    # and we delete it
    delete_staff_document(id=id)
    # when we try to get it
    # then we get an error
    with pytest.raises(NotFoundError):
        get_staff_document(id=id)
