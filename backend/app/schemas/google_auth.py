from pydantic import BaseModel


class GoogleExchangeRequest(BaseModel):
    code: str


class GoogleLinkRequest(BaseModel):
    link_token: str
