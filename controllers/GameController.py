from .Controller import Controller
from fastapi import HTTPException
from datetime import datetime
import httpx
from config import cfg
import asyncio


class GameController(Controller):
    def __init__(self):
        self.games_url = "https://api.isthereanydeal.com"
        self.api_key = cfg.STEAM_API_KEY
        self.titles = [
            "Elden Ring",
            "Half Life 2",
            "Baldur's Gate 3",
            "The witcher 3",
            "Fifa 22"
        ]

    async def get_data(self, params):
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"{self.games_url}/games/history/v2",
                params=params
            )
            response.raise_for_status()
            return response.json()

    async def get_game(self, game_id=None, shop_ids=None, start_date=None, end_date=None):
        params = {"key": self.api_key}

        if game_id:
            params["id"] = game_id

        if start_date:
            start_date_iso = datetime.strptime(start_date, "%Y-%m-%d").isoformat() + "Z"
        else:
            start_date_iso = datetime(2015,1,1).isoformat() + "Z"
        params["since"] = start_date_iso

        if shop_ids:
            params["shops"] = ",".join(shop_ids)

        try:
            response = await self.get_data(params)

            # filtrar por data final, se necessário
            if end_date:
                end_date_iso = (
                    datetime.strptime(end_date, "%Y-%m-%d").isoformat() + "Z"
                )
                end_dt = datetime.fromisoformat(end_date_iso.replace("Z", "+00:00"))

                response = [
                    entry for entry in response
                    if datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00")) <= end_dt
                ]

            if not isinstance(response, list) or not response:
                raise HTTPException(404, f"No price history found for game ID {game_id}.")

            return {
                "game_id": game_id,
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "start_date": start_date_iso,
                "end_date": end_date,
                "prices": response,
            }

        except httpx.RequestError as e:
            raise HTTPException(503, f"Error fetching data: {str(e)}")

    async def get_game_ids(self):
        async with httpx.AsyncClient(timeout=10) as client:
            tasks = []
            for title in self.titles:
                params = {"key": self.api_key, "title": title}
                tasks.append(client.get(f"{self.games_url}/games/search/v1", params=params))

            responses = await asyncio.gather(*tasks)

        result = []
        for title, resp in zip(self.titles, responses):
            data = resp.json()
            if data:
                result.append({"name": title, "id": data[0]["id"]})

        return result
