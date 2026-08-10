from enum import Enum


class RegistrationSource(Enum):
    GOOGLE = "google-oauth2"
    FACEBOOK = "facebook"
    APPLE = "apple"
    EMAIL = "email"
    AUTH0 = "auth0"
    PHONE = "phone"
