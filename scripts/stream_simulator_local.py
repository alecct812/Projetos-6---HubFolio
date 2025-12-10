"""
Simulador de streaming local para HubFólio.
Gera portfolios ALEATÓRIOS para testar a predição,
ou opcionalmente lê de um JSON local.
Envia para a API FastAPI (/predict), que publica telemetria no ThingsBoard.
"""

import json
import time
import argparse
import random
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


def generate_random_portfolio(user_id: int) -> dict:
    """Gera um portfolio com valores ALEATÓRIOS para testar a predição."""
    return {
        "user_id": user_id,
        "projetos_min": random.randint(0, 10),
        "habilidades_min": random.randint(0, 20),
        "kw_contexto": random.randint(0, 10),
        "kw_processo": random.randint(0, 10),
        "kw_resultado": random.randint(0, 10),
        "consistencia_visual_score": random.randint(0, 100),
        "bio": random.choice([True, False]),
        "contatos": random.choice([True, False]),
    }


def map_item(item: dict, idx: int) -> dict:
    """Mapeia um registro do JSON para o payload esperado pelo /predict."""
    secoes = item.get("secoes_preenchidas", {})
    palavras = item.get("palavras_chave_clareza", {})
    
    return {
        "user_id": item.get("user_id", idx + 1),
        "projetos_min": secoes.get("projetos_min", item.get("projetos_min", 3)),
        "habilidades_min": secoes.get("habilidades_min", item.get("habilidades_min", 10)),
        "kw_contexto": palavras.get("contexto", item.get("kw_contexto", 4)),
        "kw_processo": palavras.get("processo", item.get("kw_processo", 3)),
        "kw_resultado": palavras.get("resultado", item.get("kw_resultado", 4)),
        "consistencia_visual_score": item.get("consistencia_visual_score", 80),
        "bio": secoes.get("bio", item.get("bio", True)),
        "contatos": secoes.get("contatos", item.get("contatos", True)),
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
    parser.add_argument("--limit", type=int, default=5, help="Número de registros a enviar (default: 5)")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay entre envios em segundos (default: 0.5)")
    parser.add_argument("--random", action="store_true", help="Gerar portfolios ALEATÓRIOS em vez de usar o JSON")
    args = parser.parse_args()

    if args.random:
        # Modo aleatório: gera portfolios com valores randômicos
        print(f"🎲 Modo ALEATÓRIO: Gerando {args.limit} portfolios com valores randômicos")
        print(f"➡️  Enviando para {API_URL} com delay {args.delay}s\n")
        
        for i in range(args.limit):
            payload = generate_random_portfolio(user_id=i + 1)
            print(f"📤 Enviando portfolio {i+1}/{args.limit}: {payload}")
            status, body = send_prediction(payload)
            
            # Parse do response para mostrar o IQ predito
            if status == 200:
                try:
                    response_data = json.loads(body)
                    predicted_iq = response_data.get("indice_qualidade", "N/A")
                    classification = response_data.get("classificacao", "N/A")
                    print(f"✅ Resposta: IQ={predicted_iq:.2f}, Classificação={classification}")
                except:
                    print(f"✅ Status={status} Body={body}")
            else:
                print(f"❌ Erro: status={status} body={body}")
            
            if args.delay > 0 and i < args.limit - 1:
                time.sleep(args.delay)
    else:
        # Modo arquivo: lê do JSON
        path = Path(args.data)
        if not path.exists():
            print(f"❌ Arquivo não encontrado: {path}")
            return

        records = load_data(path, args.limit)
        print(f"📥 Carregados {len(records)} registros de {path}")
        print(f"➡️  Enviando para {API_URL} com delay {args.delay}s\n")

        for i, item in enumerate(records):
            payload = map_item(item, i)
            print(f"📤 Enviando portfolio {i+1}/{len(records)}: user_id={payload['user_id']}")
            status, body = send_prediction(payload)
            
            if status == 200:
                try:
                    response_data = json.loads(body)
                    predicted_iq = response_data.get("indice_qualidade", "N/A")
                    classification = response_data.get("classificacao", "N/A")
                    print(f"✅ Resposta: IQ={predicted_iq:.2f}, Classificação={classification}")
                except:
                    print(f"✅ Status={status}")
            else:
                print(f"❌ Erro: status={status} body={body}")
            
            if args.delay > 0 and i < len(records) - 1:
                time.sleep(args.delay)

    print("\n✅ Simulação concluída!")


if __name__ == "__main__":
    main()
