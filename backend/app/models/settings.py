from pydantic import BaseModel
from typing import Optional

class Settings(BaseModel):
    trading_enabled: bool = True
    quantity: int = 1
    dte: int = 0  # 0 for today, 1 for tomorrow
    otm_strikes: int = 2  # Number of OTM strikes to show
    call_strike: Optional[float] = None  # Strike price for calls
    put_strike: Optional[float] = None   # Strike price for puts