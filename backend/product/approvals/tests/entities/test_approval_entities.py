import pytest

from infra.common.exceptions import UnprocessableEntity
from product.approvals.entities.approval_entities import EntityApproval


def test_entity_approval_strips_whitespace_from_reason():
    entity = EntityApproval(reason="  Missing entries  ")

    assert entity.reason == "Missing entries"


def test_entity_approval_accepts_empty_reason():
    entity = EntityApproval(reason="")

    assert entity.reason == ""


def test_entity_approval_accepts_blank_reason_and_strips_to_empty():
    entity = EntityApproval(reason="    ")

    assert entity.reason == ""


def test_entity_approval_accepts_max_length_reason():
    entity = EntityApproval(reason="x" * 2000)

    assert entity.reason == "x" * 2000


def test_entity_approval_rejects_reason_over_max_length():
    with pytest.raises(UnprocessableEntity, match="2000 characters"):
        EntityApproval(reason="x" * 2001)


def test_entity_approval_length_check_applies_to_stripped_value():
    padded = "  " + "x" * 2000 + "  "

    entity = EntityApproval(reason=padded)

    assert entity.reason == "x" * 2000


def test_entity_approval_is_frozen():
    entity = EntityApproval(reason="some reason")

    with pytest.raises(AttributeError):
        entity.reason = "other reason"
