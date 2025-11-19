from pydantic import BaseModel, EmailStr, ConfigDict


class UserBaseSchema(BaseModel):
    name: str
    username: str
    email: EmailStr


class SignUpSchema(UserBaseSchema):
    password: str


class LoginSchema(BaseModel):
    login: str | EmailStr
    password: str


class UserReadSchema(UserBaseSchema):
    model_config = ConfigDict(from_attributes=True)


class AfterSignUpSchema(BaseModel):
    message: str
    user: UserReadSchema


class Token(BaseModel):
    access_token: str
    token_type: str


class AfterLoginSchema(Token):
    user: UserReadSchema


class TokenData(BaseModel):
    email: EmailStr
