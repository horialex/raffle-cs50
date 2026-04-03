class PasswordChangeError(Exception):
    pass


class OldPasswordRequired(PasswordChangeError):
    pass


class OldPasswordIncorrect(PasswordChangeError):
    pass
