import enum


class TokenType(enum.Enum):
    ACCESS = 'access'
    REFRESH = 'refresh'
    ASSISTENCE = 'assistence'
    VERIFICATION = 'verification'
    RESET_PASS = 'reset_pass'
