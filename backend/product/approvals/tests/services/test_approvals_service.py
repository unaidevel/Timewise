from datetime import UTC, datetime
from unittest.mock import patch

from django.test import SimpleTestCase

from product.approvals.dtos.approval_dtos import Approval
from product.approvals.exceptions import (
    ApprovalNotFoundError,
    InvalidApprovalValueError,
)
from product.approvals.services.approvals_service import ApprovalsService


def build_approval(created_by_user_id):
    return Approval(
        id=1,
        title="Budget review",
        description="Check the attached documents.",
        status="pending",
        created_by_user_id=created_by_user_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class ApprovalsServiceTests(SimpleTestCase):
    @patch(
        "product.approvals.services.approvals_service.ApprovalsRepository.create_approval"
    )
    def test_create_approval_normalizes_values_before_persisting(
        self,
        create_approval_mock,
    ):
        owner_id = 10
        expected_approval = build_approval(owner_id)
        create_approval_mock.return_value = expected_approval

        approval = ApprovalsService.create_approval(
            title="  Budget review  ",
            description="  Check the attached documents.  ",
            created_by_user_id=owner_id,
        )

        self.assertEqual(approval, expected_approval)
        create_approval_mock.assert_called_once_with(
            title="Budget review",
            description="Check the attached documents.",
            created_by_user_id=owner_id,
        )

    def test_update_approval_requires_at_least_one_field(self):
        with self.assertRaises(InvalidApprovalValueError):
            ApprovalsService.update_approval(
                1,
                10,
            )

    @patch(
        "product.approvals.services.approvals_service.ApprovalsRepository.find_by_id_for_owner"
    )
    def test_get_approval_raises_when_it_is_not_owned_or_missing(
        self,
        find_by_id_for_owner_mock,
    ):
        find_by_id_for_owner_mock.return_value = None

        with self.assertRaises(ApprovalNotFoundError):
            ApprovalsService.get_approval(1, 10)

    @patch(
        "product.approvals.services.approvals_service.ApprovalsRepository.update_approval"
    )
    def test_update_approval_normalizes_status_before_persisting(
        self,
        update_approval_mock,
    ):
        approval_id = 1
        owner_id = 10
        update_approval_mock.return_value = build_approval(owner_id)

        ApprovalsService.update_approval(
            approval_id,
            owner_id,
            status="  APPROVED  ",
        )

        update_approval_mock.assert_called_once_with(
            approval_id,
            owner_id,
            title=None,
            description=None,
            status="approved",
        )
