import string
from typing import Union, List, Optional

import pydantic
from pydantic import BaseModel, SecretStr



class EpisodeInfo(BaseModel):
    user_name: str
    user_display_name: str
