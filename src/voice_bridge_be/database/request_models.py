# Ownership & License Notice

# All code and related assets in this file are the intellectual property of
# sinceare UG (haftungsbeschränkt), Berlin, Germany.

# Released under the PolyForm Noncommercial License 1.0.0:
# https://polyformproject.org/licenses/noncommercial/1.0.0/

# - You may view, clone, and modify this code for personal, academic, or research use.
# - Commercial use, sale, or integration in commercial applications is prohibited.
# - You must include this license notice in any copies or derivatives.

# For commercial or partnership inquiries, contact: ps@sinceare.com

from typing import Optional

from pydantic import BaseModel


class AudioRequest(BaseModel):
    text: Optional[str] = None
    voice: str
