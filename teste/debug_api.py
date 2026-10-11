import requests
import json
import os
from dotenv import load_dotenv
from Backend.services.security_service import create_access_token

load_dotenv('.env')

# create token for user 1 (Master)
token = create_access_token({"id_usuario": 1})

url = "http://localhost:5050/api/reports?uniao=&associacao=AAMAR&escola=&ano=2024&bimestre=3%C2%BA+BIMESTRE"
headers = {
    "Authorization": f"Bearer {token}",
    "X-Simulate-Nivel": "",
    "X-Simulate-Uniao": "",
    "X-Simulate-Associacao": "",
    "X-Simulate-Escola": ""
}

try:
    r = requests.get(url, headers=headers)
    print(r.status_code)
    data = r.json()
    print("Visao:", data.get('visao'))
    for i, rank in enumerate(data.get('rankings', {}).get('associacao', [])):
        print(f"{i+1} - {rank.get('nome')} | proprio: {rank.get('proprio')}")
except Exception as e:
    print(e)
