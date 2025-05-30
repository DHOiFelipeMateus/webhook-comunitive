# webhook-comunitive

Autenticação JWT no Projeto FastAPI
Este documento descreve a implementação e o uso da autenticação baseada em JSON Web Tokens (JWT) para proteger endpoints sensíveis da API.
1. Visão Geral da Autenticação JWT
A autenticação JWT oferece uma forma stateless e segura de verificar a identidade dos usuários. O fluxo básico é:

Login: O cliente envia credenciais (ex: e-mail e senha) para o servidor.
Geração do Token: Se as credenciais forem válidas, o servidor gera um JWT assinado criptograficamente e o envia de volta ao cliente.
Acesso a Recursos Protegidos: O cliente armazena o JWT e o inclui no cabeçalho Authorization (formato Bearer <token>) de cada requisição subsequente para endpoints protegidos.
Validação: O servidor valida a assinatura do JWT (usando uma chave secreta) e o seu conteúdo (ex: tempo de expiração) para permitir ou negar o acesso.

2. Configuração Inicial
2.1. Dependências Necessárias
Certifique-se de que as seguintes bibliotecas Python estão instaladas em seu ambiente:
pip install passlib[bcrypt] python-jose[cryptography]


passlib: Para hashing seguro de senhas.
python-jose: Para manipulação (criação e validação) de JWTs.

2.2. Atualização do app/settings.py
Adicione as configurações relacionadas ao JWT em seu arquivo app/settings.py:
# app/settings.py

import base64
from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... (suas configurações existentes) ...

    # --- Configurações JWT ---
    JWT_SECRET_KEY: str # Chave secreta para assinar e verificar JWTs
    JWT_ALGORITHM: str = "HS256" # Algoritmo de hashing (ex: HS256)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # Tempo de vida do token em minutos

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    # ... (seus @property ou outros métodos existentes) ...
    
settings = Settings()

2.3. Configuração do .env
Adicione a JWT_SECRET_KEY ao seu arquivo .env. Esta chave deve ser longa, aleatória e mantida em segredo.
# .env

# ... (suas variáveis de ambiente existentes) ...

JWT_SECRET_KEY="sua_chave_secreta_jwt_muito_longa_e_aleatoria"
# ACCESS_TOKEN_EXPIRE_MINUTES=60 # Opcional: sobrescreva o padrão de 30 minutos

3. Estrutura do Código para Autenticação
A funcionalidade de autenticação foi segregada em módulos para melhor organização:

app/schemas/auth.py: Define os modelos Pydantic para as requisições e respostas de autenticação (ex: UserLogin, Token).
app/auth/security.py: Contém a lógica de hashing de senhas (bcrypt), criação e validação de JWTs, e as dependências FastAPI (get_current_user) para proteger as rotas.
app/api/routers/auth_router.py: Implementa o endpoint de login (POST /auth/token) que gera o JWT.
app/api/routers/scorm_router.py: A rota sensível (POST /scorm/configure-postback/{course_id}) agora utiliza a dependência de autenticação (Depends(get_current_user)) para exigir um JWT válido.
app/main.py: Inclui o novo auth_router na aplicação FastAPI.

4. Geração de Chaves e Senhas
4.1. Gerando a JWT_SECRET_KEY
É crucial que a JWT_SECRET_KEY seja gerada de forma criptograficamente segura. Use o módulo secrets do Python:
import secrets

# Gera uma string hexadecimal de 64 caracteres (32 bytes de entropia)
# Adequado para HS256 (256 bits)
secret_key = secrets.token_hex(32) 
print(secret_key)

Copie a saída e cole-a no seu arquivo .env para a variável JWT_SECRET_KEY.
4.2. Gerando o Hash da Senha Admin
Para o exemplo de autenticação, um usuário "admin" com credenciais hardcoded é utilizado (admin@example.com). Em um ambiente de produção real, as senhas seriam armazenadas em um banco de dados após serem hashadas.
Para gerar o hash da senha de teste:
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed_password = pwd_context.hash("sua_senha_admin_segura") # Substitua pela sua senha desejada
print(hashed_password)

Copie o hash gerado e cole-o na variável ADMIN_USER_PASSWORD_HASHED dentro do arquivo app/auth/security.py.
5. Fluxo de Autenticação na Prática
Assumindo que sua aplicação FastAPI está rodando (ex: uvicorn app.main:app --reload), vamos simular o fluxo de autenticação.
5.1. Utilizando o Swagger UI (/docs)

Acesse o Swagger UI: Abra seu navegador e navegue até http://localhost:8000/docs.

Obtenha o Token de Acesso (Login):

Na seção Authentication, expanda o endpoint POST /auth/token.
Clique em "Try it out".
No campo username, digite admin@example.com.
No campo password, digite a senha em texto claro que você usou para gerar o hash (ex: sua_senha_admin_segura).
Clique em "Execute".
Copie o access_token completo da resposta JSON (o valor da string).


Autorize no Swagger UI:

No topo da página do Swagger UI, clique no botão "Authorize".
Na janela pop-up, no campo Value, digite Bearer  (com um espaço no final) seguido do access_token que você copiou.
Exemplo: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBleGFtcGxlLmNvbSIsImV4cCI6MTcwMjQ0NTAwMH0.SomeniceHashGeneratedByJwt
Clique em "Authorize" e depois em "Close".
A partir de agora, todas as requisições de endpoints protegidos feitas pelo Swagger UI incluirão este cabeçalho.


Acesse a Rota Protegida:

Na seção SCORM Webhook Configuration, expanda o endpoint POST /scorm/configure-postback/{course_id}.
Clique em "Try it out".
No campo course_id, digite um ID de curso de teste (ex: my-test-course-id).
Clique em "Execute".
A resposta esperada será um HTTP 200 OK com o JSON de sucesso. Se o token estiver ausente, inválido ou expirado, você receberá um HTTP 401 Unauthorized.


5.2. Exemplo de Requisição em Python
import requests
import json

# --- Configurações ---
BASE_URL = "http://localhost:8000"
AUTH_USERNAME = "admin@example.com"
AUTH_PASSWORD = "sua_senha_admin_segura" # A senha em texto claro
COURSE_ID_TO_CONFIGURE = "my-new-scorm-course-123"

# --- Passo 1: Obter o Token de Acesso ---
print("--- Passo 1: Tentando obter token de acesso ---")
token_url = f"{BASE_URL}/auth/token"
login_data = {
    "username": AUTH_USERNAME,
    "password": AUTH_PASSWORD
}

# O endpoint /auth/token com OAuth2PasswordRequestForm espera 'data' (form-urlencoded)
response_login = requests.post(token_url, data=login_data)

if response_login.status_code == 200:
    token_info = response_login.json()
    access_token = token_info["access_token"]
    token_type = token_info["token_type"]
    print(f"Token obtido com sucesso! Tipo: {token_type}, Token: {access_token[:30]}...")
else:
    print(f"Erro ao obter token. Status: {response_login.status_code}, Resposta: {response_login.text}")
    access_token = None
    token_type = None

# --- Passo 2: Acessar a Rota Protegida ---
if access_token:
    print("\n--- Passo 2: Tentando configurar postback SCORM com o token ---")
    configure_url = f"{BASE_URL}/scorm/configure-postback/{COURSE_ID_TO_CONFIGURE}"
    
    # Monta o cabeçalho de autorização
    headers = {
        "Authorization": f"{token_type.capitalize()} {access_token}",
        "Accept": "application/json"
    }

    response_configure = requests.post(configure_url, headers=headers)

    if response_configure.status_code == 200:
        print("Configuração de postback SCORM bem-sucedida!")
        print("Resposta:")
        print(json.dumps(response_configure.json(), indent=2))
    elif response_configure.status_code == 401:
        print("Erro: Não autorizado. O token pode estar inválido ou expirado.")
        print(f"Resposta: {response_configure.text}")
    elif response_configure.status_code == 422:
        print("Erro: Entidade não processável (validação de dados).")
        print(f"Resposta: {response_configure.text}")
    else:
        print(f"Erro ao configurar postback. Status: {response_configure.status_code}, Resposta: {response_configure.text}")
else:
    print("\nNão foi possível configurar o postback SCORM pois o token de acesso não foi obtido.")


Com este guia, você e sua equipe poderão entender, implementar e testar a autenticação JWT de forma eficaz em seu projeto FastAPI.

