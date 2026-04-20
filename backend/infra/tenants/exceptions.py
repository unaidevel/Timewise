class TenantError(Exception):
    pass


class TenantNotFoundError(TenantError):
    pass


class TenantAlreadyExistsError(TenantError):
    pass


class InvalidTenantNameError(TenantError):
    pass


class InvalidTenantSlugError(TenantError):
    pass


class MemberAlreadyExistsError(TenantError):
    pass


class MemberNotFoundError(TenantError):
    pass


class InvalidMemberRoleError(TenantError):
    pass
