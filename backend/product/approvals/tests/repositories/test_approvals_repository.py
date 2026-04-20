from django.test import TestCase

from infra.authz.services.auth_service import AuthService
from product.approvals.repositories.approvals_repository import ApprovalsRepository


class ApprovalsRepositoryTests(TestCase):
    def setUp(self) -> None:
        self.owner = AuthService.register_user(
            email="owner@example.com",
            full_name="Owner User",
            password="SecurePass123!",
        )
        self.other_user = AuthService.register_user(
            email="other@example.com",
            full_name="Other User",
            password="SecurePass123!",
        )

    def test_create_and_list_are_scoped_to_owner(self):
        owner_approval = ApprovalsRepository.create_approval(
            title="Budget sign-off",
            description="Review the April budget update.",
            created_by_user_id=self.owner.id,
        )
        ApprovalsRepository.create_approval(
            title="Other approval",
            description="This belongs to another user.",
            created_by_user_id=self.other_user.id,
        )

        owner_approvals = ApprovalsRepository.list_approvals_for_owner(self.owner.id)

        self.assertEqual(len(owner_approvals), 1)
        self.assertEqual(owner_approvals[0], owner_approval)
        self.assertEqual(owner_approvals[0].created_by_user_id, self.owner.id)

    def test_update_and_delete_require_the_owner(self):
        approval = ApprovalsRepository.create_approval(
            title="Vendor onboarding",
            description="Initial review.",
            created_by_user_id=self.owner.id,
        )

        self.assertIsNone(
            ApprovalsRepository.find_by_id_for_owner(
                approval.id,
                self.other_user.id,
            )
        )
        self.assertIsNone(
            ApprovalsRepository.update_approval(
                approval.id,
                self.other_user.id,
                title="Updated title",
            )
        )
        self.assertEqual(
            ApprovalsRepository.delete_approval(approval.id, self.other_user.id),
            0,
        )
        self.assertEqual(
            ApprovalsRepository.delete_approval(approval.id, self.owner.id),
            1,
        )
