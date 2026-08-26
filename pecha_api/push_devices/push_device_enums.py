import enum

from sqlalchemy import Enum


class PushPlatform(enum.Enum):
    ANDROID = "ANDROID"
    IOS = "IOS"


PushPlatformEnum = Enum(PushPlatform, name="push_platform")
