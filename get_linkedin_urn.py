"""
Script auxiliar para obter seu LinkedIn URN e testar o token.
Execute UMA VEZ localmente antes de configurar o GitHub Actions.

Uso:
    LINKEDIN_TOKEN=seu_token python get_linkedin_urn.py
"""

import os
import requests

TOKEN = "AQXB4vOUJG1lebQimuVMK0BFDDTvzMnYj1oDBb0JjwqcNJuP6B4lDO6WWLSimYtvsJuabn70vyFRoMcqxbX3SKj6BM93mJRIwQ65-zwnBSX_yE4tANBi25HXvSz6TfpMOq8ohFwk4Hs7yQVz3b9S5RjLKrB1sjJSb1W0NQjiNIy_n5WIB9MRcG5bLUeDcBE4C1SPXXJhh1vhvyPL_lXfHgG3nt3-k9TxPxvVRNCZbmWIZEwHihJZBD5T7PPPEXdOx2pK0_RlFkuRcUELK8nB0AXX_hw7E2GoPJilWVu-PRvScWdgE_Cs0TmGK5UoFmdx5MnIaByBygLaSSOCD7wiF9IlFCgDeA"

if not TOKEN:
    print("❌ Defina a variável LINKEDIN_TOKEN antes de rodar.")
    print("   Exemplo: LINKEDIN_TOKEN=xxxx python get_linkedin_urn.py")
    exit(1)

print("🔍 Buscando seus dados do LinkedIn...\n")

response = requests.get(
    "https://api.linkedin.com/v2/userinfo",
    headers={"Authorization": f"Bearer {TOKEN}"},
    timeout=10
)

if response.status_code != 200:
    print(f"❌ Erro {response.status_code}: {response.text}")
    print("\nPossíveis causas:")
    print("  • Token expirado (tokens duram 2 meses)")
    print("  • Token sem escopo 'openid' habilitado")
    exit(1)

data = response.json()

print("✅ Token válido! Seus dados:\n")
print(f"  Nome  : {data.get('name', 'N/A')}")
print(f"  Email : {data.get('email', 'N/A')}")
print(f"  URN   : {data.get('sub', 'N/A')}")
print()
print("=" * 50)
print(f"  Copie este valor para o secret LINKEDIN_URN:")
print(f"  👉  {data.get('sub', '')}")
print("=" * 50)