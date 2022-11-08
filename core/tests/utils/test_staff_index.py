from unittest import skip

import pytest
from opensearchpy.exceptions import NotFoundError

from core.utils.staff_index import (
    delete_staff_document,
    get_staff_document,
    update_staff_document,
)


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
    # when we try to extend it upsert
    update_staff_document(id=id, staff_document={"hair_colour": "blonde"})
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
