class AuthError(Exception):
    pass


class InvalidCredentialsError(AuthError):
    pass


class EmailAlreadyExistsError(AuthError):
    pass


class InvalidAuthValueError(AuthError):
    pass


class InvalidEmailError(InvalidAuthValueError):
    pass


class InvalidFullNameError(InvalidAuthValueError):
    pass


class InvalidPasswordError(InvalidAuthValueError):
    pass


class WeakPasswordError(AuthError):
    def __init__(self, messages: list[str]):
        self.messages = messages
        super().__init__(" ".join(messages))


class TooManyLoginAttemptsError(AuthError):
    pass
