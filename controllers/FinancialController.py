from fastapi import  HTTPException
from .Controller import Controller
import imfp
import pandas as pd
from datetime import datetime

class FinancialController(Controller):
    def __init__(self):
        self.indicators_info = {
            "PCPIPCH": "taxa de inflação, média de preços consumidores (percentual anual)",
            "NGDPDPC": "PIB per capita, preços atuais (dólares americanos)",
            "PPPPC": "PIB per capita, PPP (dólares internacionais atuais)",
            "NGDP_RPCH": "PIB, preços constantes (percentual anual)",
            "LUR": "taxa de desemprego (percentual do total da força de trabalho)",
        }

    def get_data(self, 
        countries:str,
        indicators:list[str],
        end_year:int,
        start_year:int = 2021
    ):
        # Fetch data from IMF World Economic Outlook (WEO) database
        df = imfp.imf_dataset(
            database_id="WEO",
            indicator=indicators,
            country=countries,
        )

        if df is not None and not df.empty:
            # Standardize column names - handle different possible names
            # df = df.drop("frequency")
            columns = df.columns
            columns = [col.lower().replace('@','') for col in columns]
            rep_cols = [
                {'from':'time_period','to':'year'},
                {'from':'ref_area','to':'country'},
                {'from':'obs_value','to':'value'}
            ]
            for repcol in rep_cols:
                if(repcol['from'] in columns):
                    index_col = columns.index(repcol['from'])
                    columns[index_col] = repcol['to']
            df.columns = columns

            df = df[df['year']>=start_year]
            if(end_year): df = df[df['year'] <= end_year]

        return self.format_for_api(df)  
          
    def format_for_api(self, df):
        """Formata dados para consumo na API como JSON"""

        if df.empty:
            return {
                "error": "Nenhum dado disponível",
                "message": "Falha ao coletar dados do IMF",
            }

        # Validate required columns
        required_cols = ["country", "year", "indicator", "value"]
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            return {
                "error": "Colunas obrigatórias ausentes",
                "missing": missing_cols,
                "available": df.columns.tolist(),
            }

        # Clean and convert data types
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["year", "value"])

        # Pivot data so each country-year has all indicators
        pivot_df = df.pivot_table(
            index=["country", "year"],
            columns="indicator",
            values="value",
            aggfunc="first",
        ).reset_index()

        # Build JSON structure
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
            "data": {},
        }

        # Group by country
        for country in pivot_df["country"].unique():
            country_data = pivot_df[pivot_df["country"] == country].copy()
            country_data = country_data.sort_values("year")

            result["data"][country] = []

            for _, row in country_data.iterrows():
                year_data = {
                    "period": int(row["year"]),
                    "period_type": "year",
                    "indicators": {},
                }

                # Add all economic indicators
                for col in country_data.columns:
                    if col not in ["country", "year"] and pd.notna(row[col]):
                        year_data["indicators"][col] = float(row[col])

                result["data"][country].append(year_data)

        return result
    
    def get_indicators(self, 
            countries = [],
            indicators= [],
            end_year = None,
            start_year = None,
        ):
        countries = ','.join(countries) if(countries and len(countries) > 0) else []
        indicators = indicators if(indicators and len(indicators) > 0) else list(self.indicators_info.keys())
        
        financial_data = self.get_data(
            countries = countries,
            indicators = indicators,
            start_year = start_year,
            end_year = end_year
        ) 
        if "error" in financial_data:
            raise HTTPException(
                status_code=404,
                detail=financial_data["error"]
            )
        return financial_data 
    
    def get_indicators_ids(self):
        response = [{'input_code':key, 'description':self.indicators_info[key]} for key in self.indicators_info.keys()]
        return response
    
    def get_countries_id(self):
        dados = imfp.imf_parameters(database_id="WEO")
        dados = dados['country'].reset_index(drop=True)
        return [
            {k: str(v) for k, v in row.items()} 
            for row in dados.to_dict(orient="records")
        ]