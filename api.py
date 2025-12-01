from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from models.game import GameHistoryResponse
from models.indicator import EconomicIndicatorsResponse
from controllers.GameController import GameController
from controllers.FinancialController import FinancialController
import uvicorn
from typing import Optional

app = FastAPI(
    title="Historico de Preços de Jogos API",
    description="API para acesso ao histórico de preços de jogos",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

game_controller = GameController()
financial_controller = FinancialController()

@app.get(
    "/prices",
    response_model=GameHistoryResponse,
    tags=["Games"]
)
async def get_all_prices(
    game_id:str = None,
    shop_ids:Optional[list[str]] = Query(None),
    start_date:Optional[str] = None,
    end_date:Optional[str] = None
):
    return await game_controller.get_game(
        game_id,
        shop_ids, 
        start_date,
        end_date
    )

@app.get(
   "/games_list",
   response_model = list[dict[str,str]],
   tags=['Games']
)
async def get_games_list():
    return await game_controller.get_game_ids()

@app.get(
    "/economic-indicators",
    response_model=EconomicIndicatorsResponse,
    tags=["Economic Indicators"],
)
async def get_economic_indicators(
    countries:Optional[list[str]] = Query(None),
    indicators:list[str] = Query(None),
    end_year:Optional[str] = None,
    start_year:Optional[str] = 2021
):
    return await financial_controller.get_indicators(
        indicators=indicators,
        countries=countries,
        end_year=end_year,
        start_year=start_year
    )

@app.get(
    "/indicators_list",
    response_model = list[dict[str,str]],
    tags=["Economic Indicators"]
)
async def get_indicators_list():
    return await financial_controller.get_indicators_ids()

@app.get(
    "/countries_list",
    response_model=list[dict[str,str]],
    tags=["Economic Indicators"]
)
async def get_countries_list():
    return await financial_controller.get_countries_id()

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
