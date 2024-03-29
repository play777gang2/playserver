from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pynubank import Nubank, NuException, CertificateGenerator, HttpClient
import os
import random
import string
from colorama import init, Fore, Style

app = FastAPI()

def generate_random_id() -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))

def save_cert(cert, name):
    path = os.path.join(os.getcwd(), name)
    with open(path, 'wb') as cert_file:
        cert_file.write(cert.export())

class HttpClientWithPassword(HttpClient):
    def _cert_args(self):
        return {'pkcs12_data': self._cert, 'pkcs12_password': 'nubank'}

junto = {}

@app.get("/certificadoleve/{cpf}/{senha}")
def certificadoleve(cpf: str, senha: str):
    init()

    device_id = generate_random_id()
    generator = CertificateGenerator(cpf, senha, device_id)

    junto[cpf] = {"cpf": cpf, "chave": generator}

    try:
        email = generator.request_code()
    except NuException:
        raise HTTPException(status_code=500, detail="Erro ao solicitar código.")

    return {"email": email}

@app.get("/leve/{codigo}/{cpf}")
def leve(codigo: str, cpf: str):
    if cpf not in junto:
        raise HTTPException(status_code=404, detail="CPF não encontrado.")

    item = junto[cpf]

    if "chave" not in item:
        raise HTTPException(status_code=500, detail="Chave não encontrada para este CPF.")

    chave = item["chave"]

    try:
        cert1, cert2 = chave.exchange_certs(codigo)
        save_cert(cert1, f"{codigo}.p12")
        return {"mensagem": "Play7Server - Certificado Gerado com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao gerar certificado. Verifique os dados e tente novamente.")
