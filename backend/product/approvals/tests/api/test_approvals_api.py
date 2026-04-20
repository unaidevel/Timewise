from django.test import TestCase
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from starlette.requests import Request

from infra.authz.api import router as auth_router
from infra.authz.api.dependencies import get_current_user
from infra.authz.dtos.dtos import LoginRequest, RegisterRequest
from product.approvals.api import router as approvals_router
from product.approvals.dtos.dtos import (
    CreateApprovalRequest,
    UpdateApprovalRequest,
)


def build_request(path: str, client_host: str = "127.0.0.1") -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": path,
            "headers": [],
            "client": (client_host, 1234),
        }
    )


class ApprovalsApiTests(TestCase):
    def _authenticate_user(self, *, email: str, full_name: str) -> HTTPAuthorizationCredentials:
        auth_router.register(
            RegisterRequest(
                email=email,
                full_name=full_name,
                password="SecurePass123!",
            )
        )
        login_response = auth_router.login_user(
            LoginRequest(email=email, password="SecurePass123!"),
            build_request("/api/v1/auth/login"),
        )

        return HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=login_response.access_token,
        )

    def test_approvals_endpoints_require_authentication(self):
        with self.assertRaises(HTTPException) as exc:
            get_current_user(None)

        self.assertEqual(exc.exception.status_code, 401)

    def test_authenticated_crud_is_scoped_to_the_current_user(self):
        owner_credentials = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner User",
        )
        other_credentials = self._authenticate_user(
            email="other@example.com",
            full_name="Other User",
        )
        owner_user = get_current_user(owner_credentials)
        other_user = get_current_user(other_credentials)

        created_approval = approvals_router.create_approval(
            CreateApprovalRequest(
                title="  Budget review  ",
                description="  Check docs before approval.  ",
            ),
            current_user=owner_user,
        )
        self.assertEqual(created_approval.title, "Budget review")
        self.assertEqual(
            created_approval.description,
            "Check docs before approval.",
        )

        owner_approvals = approvals_router.list_approvals(current_user=owner_user)
        self.assertEqual(len(owner_approvals), 1)

        with self.assertRaises(HTTPException) as get_exc:
            approvals_router.get_approval(
                created_approval.id,
                current_user=other_user,
            )
        self.assertEqual(get_exc.exception.status_code, 404)

        updated_approval = approvals_router.update_approval(
            created_approval.id,
            UpdateApprovalRequest(status="  APPROVED  "),
            current_user=owner_user,
        )
        self.assertEqual(updated_approval.status, "approved")

        with self.assertRaises(HTTPException) as delete_exc:
            approvals_router.delete_approval(
                created_approval.id,
                current_user=other_user,
            )
        self.assertEqual(delete_exc.exception.status_code, 404)

        approvals_router.delete_approval(
            created_approval.id,
            current_user=owner_user,
        )
        final_approvals = approvals_router.list_approvals(current_user=owner_user)
        self.assertEqual(final_approvals, [])
