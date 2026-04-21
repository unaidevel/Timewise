class WorkforceError(Exception):
    pass


class DepartmentNotFoundError(WorkforceError):
    pass


class DepartmentAlreadyExistsError(WorkforceError):
    pass


class InvalidDepartmentNameError(WorkforceError):
    pass


class RoleNotFoundError(WorkforceError):
    pass


class RoleAlreadyExistsError(WorkforceError):
    pass


class InvalidRoleNameError(WorkforceError):
    pass


class EmployeeNotFoundError(WorkforceError):
    pass


class EmployeeAlreadyExistsError(WorkforceError):
    pass


class InvalidEmployeeDataError(WorkforceError):
    pass
