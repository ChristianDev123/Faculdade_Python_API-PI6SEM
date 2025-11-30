from .Controller import Controller
from requests import get, exceptions
from config import cfg
from fastapi import  HTTPException
from datetime import datetime

class GameController(Controller):
    def __init__(self):
        self.games_url = "https://api.isthereanydeal.com"
        self.params = {'key':cfg.STEAM_API_KEY}
        self.titles = ['Elden Ring', "Half Life 2", "Baldur's Gate 3", "The witcher 3", "Fifa 22"]

    def get_data(self, params):
        return get(f"{self.games_url}/games/history/v2", params=params)

    def get_game(self, game_id=None, shop_ids=[], start_date=None, end_date=None):
        params = self.params
        if(game_id): params['id'] = game_id
        if(start_date): 
            start_date = datetime.strptime(start_date, "%Y-%m-%d").isoformat()
            params['since'] = start_date+"Z"
        
        if(shop_ids and len(shop_ids) > 0): params['shops'] = ','.join(shop_ids)

        try:
            result = self.get_data(params) 
            result.raise_for_status()
            response = result.json()
            if(end_date):
                end_date = datetime.strptime(end_date, "%Y-%m-%d").isoformat()+"Z"
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                response = [
                    entry for entry in response
                    if datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00")) <= end_dt
                ]

            if not isinstance(response, list) or not response:
                raise HTTPException(
                    status_code=404, 
                    detail=f"No price history found for game ID {game_id}."
                )
       
            return {
                "game_id": game_id,
                "last_updated": datetime.today().isoformat() + "Z",
                "start_date": start_date,
                "end_date": end_date,
                "prices": response,
            }
        
        except exceptions.RequestException as e:
            raise HTTPException(
                status_code=503,
                detail=f"Error fetching data from API: {e}"
            )
    
    def get_game_ids(self):
        response = []
        for title in self.titles:
            self.params['title'] = title
            result = get(f"{self.games_url}/games/search/v1", self.params)
            game = result.json()[0]
            id = game['id']
            response.append({"name":title,"id":id})
        return response