from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class Game(BaseModel):
    timestamp: str
    shop: Dict[str, Any]
    deal: Dict[str, Any]

class GameHistoryResponse(BaseModel):
    game_id: str
    last_updated: str
    start_date: Optional[str]
    end_date: Optional[str]
    prices: List[Game]    