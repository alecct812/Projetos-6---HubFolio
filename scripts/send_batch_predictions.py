"""
Envia predições em lote para o FastAPI (/predict), gerando telemetria no ThingsBoard.
Lê o arquivo data/hubfolio_mock_data.json e envia cada item.
"""

import json
import requests

URL = "http://localhost:8001/predict"
DATA_PATH = "data/hubfolio_mock_data.json"


def normalize_item(item, idx):
    # Adapte os campos conforme seu JSON; use defaults se não houver.
    return {
        "user_id": item.get("user_id", idx + 1),
        "projetos_min": item.get("projetos_min", 3),
        "habilidades_min": item.get("habilidades_min", 10),
        "kw_contexto": item.get("kw_contexto", 4),
        "kw_processo": item.get("kw_processo", 3),
        "kw_resultado": item.get("kw_resultado", 4),
        "consistencia_visual_score": item.get("consistencia_visual_score", 80),
        "bio": item.get("bio", True),
        "contatos": item.get("contatos", True),
    }


def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for i, item in enumerate(data):
        payload = normalize_item(item, i)
        try:
            r = requests.post(URL, json=payload, timeout=10)
            print(f"{i:04d} status={r.status_code} body={r.text}")
        except Exception as e:
            print(f"{i:04d} error={e}")


if __name__ == "__main__":
    main()

