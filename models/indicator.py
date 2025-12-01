from pydantic import BaseModel
from typing import Dict, Any, List, Optional


class EconomicDataPoint(BaseModel):
    period: int
    period_type: str
    country:str
    indicators: List[Dict[str, Optional[str|float]]]

class EconomicIndicatorsResponse(BaseModel):
    metadata: Dict[str, Any]
    data: List[EconomicDataPoint]
