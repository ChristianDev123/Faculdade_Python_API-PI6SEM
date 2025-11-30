from pydantic import BaseModel
from typing import Dict, Any, List, Optional


class EconomicDataPoint(BaseModel):
    period: int
    period_type: str
    indicators: Dict[str, Optional[float]]

class EconomicIndicatorsResponse(BaseModel):
    metadata: Dict[str, Any]
    data: Dict[str, List[EconomicDataPoint]]
