

class AuthError(Exception):
    pass


class InvalidCredentialsError(AuthError):
    pass


class EmailAlreadyExistsError(AuthError):
    pass