import requests

url = "https://gist.githubusercontent.com/rogernogueira/10c169adf7f5d5810db3dacbf12aaad8/raw/bad45b04548f7ecc7348d4859e848504cdb7375c/engajamento_alunos.json"
arquivo_saida = "engajamento_alunos.json"

response = requests.get(url, stream=True)

response.raise_for_status()  # Gera exceção se houver erro HTTP

with open(arquivo_saida, "wb") as f:
    for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)

print(f"Arquivo salvo como: {arquivo_saida}")
