"""
Simulador de streaming local para HubFólio.
Lê dados de um JSON local e envia para a API FastAPI (/predict),
que já publica a telemetria no ThingsBoard.
Não usa Snowflake nem S3.
"""

import json
import time
import argparse
import requests
from pathlib import Path

# Caminhos/URLs padrão
DATA_PATH = Path("data/hubfolio_mock_data.json")
API_URL = "http://localhost:8001/predict"


def load_data(path: Path, limit: int | None = None) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if limit:
        data = data[:limit]
    return data


def map_item(item: dict, idx: int) -> dict:
    """Mapeia um registro do JSON para o payload esperado pelo /predict."""
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


def send_prediction(payload: dict) -> tuple[int, str]:
    try:
        r = requests.post(API_URL, json=payload, timeout=10)
        return r.status_code, r.text
    except Exception as e:
        return 0, str(e)


def main():
    parser = argparse.ArgumentParser(description="Simulador de streaming local (HubFólio)")
    parser.add_argument("--data", default=str(DATA_PATH), help="Caminho do JSON de entrada")
    parser.add_argument("--limit", type=int, default=None, help="Número máximo de registros")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay entre envios (s)")
    args = parser.parse_args()

    path = Path(args.data)
    if not path.exists():
        print(f"❌ Arquivo não encontrado: {path}")
        return

    records = load_data(path, args.limit)
    print(f"📥 Carregados {len(records)} registros de {path}")
    print(f"➡️  Enviando para {API_URL} com delay {args.delay}s\n")

    for i, item in enumerate(records):
        payload = map_item(item, i)
        status, body = send_prediction(payload)
        print(f"{i:04d} status={status} body={body}")
        if args.delay > 0 and i < len(records) - 1:
            time.sleep(args.delay)


if __name__ == "__main__":
    main()

