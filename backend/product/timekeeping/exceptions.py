class TimekeepingError(Exception):
    pass


class PeriodNotFoundError(TimekeepingError):
    pass


class PeriodAlreadyExistsError(TimekeepingError):
    pass


class PeriodAlreadyLockedError(TimekeepingError):
    pass


class InvalidPeriodDatesError(TimekeepingError):
    pass


class TimeReportNotFoundError(TimekeepingError):
    pass


class TimeReportAlreadyExistsError(TimekeepingError):
    pass


class InvalidTimeReportStatusTransitionError(TimekeepingError):
    pass


class TimeReportNotEditableError(TimekeepingError):
    pass


class TimeEntryNotFoundError(TimekeepingError):
    pass


class InvalidTimeEntryError(TimekeepingError):
    pass
