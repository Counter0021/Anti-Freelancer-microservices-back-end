import re

from pydantic import BaseModel, validator, EmailStr


class Message(BaseModel):
    """ Message """

    msg: str


class Password(BaseModel):
    """ Password """

    password: str
    confirm_password: str

    @validator('password')
    def validate_password(cls, password):
        """ Validate password """

        reg = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,20}$'
        if not re.search(reg, password):
            raise ValueError('Password invalid')
        return password

    @validator('confirm_password')
    def validate_confirm_password(cls, confirm_password, values, **kwargs):
        """ Validate confirm password """

        if 'password' in values and confirm_password != values['password']:
            raise ValueError('Passwords do not match')
        return confirm_password


class Register(Password):
    """ Register """

    username: str
    email: EmailStr
    freelancer: bool = False


class VerificationCreate(BaseModel):
    """ Verification create """

    user_id: int
    link: str


class AccessToken(BaseModel):
    """ Access token """

    access_token: str
    type: str


class RefreshToken(BaseModel):
    """ Refresh token """

    refresh_token: str
    type: str


class Tokens(AccessToken, RefreshToken):
    """ Tokens """

    pass
