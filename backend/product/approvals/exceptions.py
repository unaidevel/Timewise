class ApprovalError(Exception):
    pass


class ApprovalNotFoundError(ApprovalError):
    pass


class InvalidApprovalValueError(ApprovalError):
    pass
