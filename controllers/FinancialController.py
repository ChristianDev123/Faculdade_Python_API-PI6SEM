from fastapi import HTTPException
from .Controller import Controller
import imfp
import pandas as pd
from datetime import datetime
import asyncio

class FinancialController(Controller):
    def __init__(self):
        self.indicators_info = {
            "PCPIPCH": "taxa de inflação (percentual anual)",
            "NGDPDPC": "PIB per capita (dólares americanos)",
            "PPPPC": "PIB per capita (dólares internacionais atuais)",
            "NGDP_RPCH": "PIB (percentual anual)",
            "LUR": "taxa de desemprego (percentual do total da força de trabalho)",
        }

    async def get_data(self, countries: str, indicators: list[str], end_year: int, start_year: int = 2021):
        """
        Executa imfp e pandas em thread separada para não travar o loop async.
        """

        df = await asyncio.to_thread(
            imfp.imf_dataset,
            "WEO",
            indicator=indicators,
            country=countries
        )

        if df is not None and not df.empty:
            df = df.copy()
            columns = [col.lower().replace('@', '') for col in df.columns]

            # renomear colunas
            rep_cols = [
                {'from': 'time_period', 'to': 'year'},
                {'from': 'ref_area', 'to': 'country'},
                {'from': 'obs_value', 'to': 'value'}
            ]

            for rep in rep_cols:
                if rep['from'] in columns:
                    idx = columns.index(rep['from'])
                    columns[idx] = rep['to']

            df.columns = columns

            df = df[df["year"] >= start_year]
            if end_year:
                df = df[df["year"] <= end_year]

        return await asyncio.to_thread(self.format_for_api, df)

    def format_for_api(self, df):
        """Formata dados para consumo API (CPU-bound: ok rodar síncrono)"""
        if df.empty:
            return {
                "error": "Nenhum dado disponível",
                "message": "Falha ao coletar dados do IMF",
            }

        required_cols = ["country", "year", "indicator", "value"]
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            return {
                "error": "Colunas obrigatórias ausentes",
                "missing": missing_cols,
                "available": df.columns.tolist(),
            }

        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["year", "value"])

        pivot_df = df.pivot_table(
            index=["country", "year"],
            columns="indicator",
            values="value",
            aggfunc="first",
        ).reset_index()

        result = {
            "metadata": {
                "source": "IMF (International Monetary Fund)",
                "database": "World Economic Outlook",
                "indicators": {
                    code: self.indicators_info.get(code, code)
                    for code in df["indicator"].unique()
                },
                "countries": sorted(df["country"].unique().tolist()),
                "year_range": {
                    "start": int(df["year"].min()),
                    "end": int(df["year"].max()),
                },
                "total_records": len(pivot_df),
                "generated_at": datetime.now().isoformat(),
            },
            "data": [],
        }

        for country in pivot_df["country"].unique():
            country_data = pivot_df[pivot_df["country"] == country].copy()
            country_data = country_data.sort_values("year")
            for _, row in country_data.iterrows():
                year_data = {
                    "period": int(row["year"]),
                    "period_type": "year",
                    'country': row['country'],
                    "indicators": [{
                        'code': col, 
                        'value': row[col]
                    } for col in country_data.columns if col not in ['year','country'] and pd.notna(row[col])],
                }

                result["data"].append(year_data)

        return result

    async def get_indicators(self, countries=None, indicators=None, end_year=None, start_year=None):
        indicators = indicators if indicators else list(self.indicators_info.keys())
        if(not start_year): start_year = '2021'
        financial_data = await self.get_data(
            countries=countries,
            indicators=indicators,
            start_year=start_year,
            end_year=end_year
        )

        if "error" in financial_data:
            raise HTTPException(status_code=404, detail=financial_data["error"])

        return financial_data

    async def get_indicators_ids(self):
        return [
            {"input_code": key, "description": self.indicators_info[key]}
            for key in self.indicators_info.keys()
        ]

    async def get_countries_id(self):
        df = await asyncio.to_thread(imfp.imf_parameters, "WEO")
        df = df["country"].reset_index(drop=True)
        records = df.to_dict(orient="records")
        return [{k: str(v) for k, v in row.items()} for row in records]
