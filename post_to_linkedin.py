"""
LinkedIn Auto Poster
Gera posts sobre seus projetos usando Google Gemini e publica no LinkedIn.
Disparado automaticamente pelo GitHub Actions a cada push.
"""

import os
import json
import requests
import subprocess
import sys

# ── Configurações (via variáveis de ambiente) ────────────────────────────────
GEMINI_API_KEY   = os.environ["GEMINI_API_KEY"]
LINKEDIN_TOKEN   = os.environ["LINKEDIN_TOKEN"]
LINKEDIN_URN     = os.environ["LINKEDIN_URN"]       # ex: "abc123XYZ"

# ── Informações do push (injetadas pelo GitHub Actions) ──────────────────────
REPO_NAME        = os.environ.get("GITHUB_REPOSITORY", "meu-projeto")
COMMIT_MSG       = os.environ.get("COMMIT_MESSAGE", "Atualização no projeto")
BRANCH           = os.environ.get("GITHUB_REF_NAME", "main")
REPO_URL         = f"https://github.com/{REPO_NAME}"


def get_changed_files() -> str:
    """Retorna lista de arquivos alterados no último commit."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            capture_output=True, text=True
        )
        files = result.stdout.strip().split("\n")
        return ", ".join(files[:5])  # máximo 5 arquivos
    except Exception:
        return "vários arquivos"


def generate_post_with_gemini(commit_msg: str, repo: str, files: str) -> str:
    """Chama a API do Gemini para gerar o texto do post, com retry automático."""
    import time

    prompt = f"""
Você é um desenvolvedor de software brasileiro que compartilha atualizações 
dos seus projetos no LinkedIn de forma autêntica e engajante.

Crie um post em português para o LinkedIn com base nesta atualização de código:

- Repositório: {repo}
- Mensagem do commit: {commit_msg}
- Arquivos modificados: {files}
- Branch: {BRANCH}
- Link do repositório: {REPO_URL}

Regras:
1. Escreva em primeira pessoa, tom natural e entusiasmado
2. Máximo 150 palavras
3. Inclua 3 a 5 hashtags relevantes ao final (ex: #Python #OpenSource)
4. Mencione o link do repositório de forma fluida
5. NÃO use emojis em excesso (máximo 2)
6. Foque no aprendizado ou valor técnico da mudança

Retorne APENAS o texto do post, sem aspas nem explicações.
"""

    # Tenta modelos em ordem até um funcionar
    models = [
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash",
        "gemini-1.5-flash-latest",
    ]

    headers = {"Content-Type": "application/json"}
    params  = {"key": GEMINI_API_KEY}
    body    = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 400, "temperature": 0.8}
    }

    for attempt in range(3):  # até 3 tentativas
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            try:
                print(f"   Tentando modelo: {model} (tentativa {attempt + 1})")
                response = requests.post(url, headers=headers, params=params, json=body, timeout=30)
                if response.status_code == 429:
                    print(f"   ⏳ Limite atingido em {model}, tentando próximo...")
                    continue
                response.raise_for_status()
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception as e:
                print(f"   ⚠️ Erro em {model}: {e}")
                continue

        print(f"   Aguardando 30s antes de tentar novamente...")
        time.sleep(30)

    raise Exception("❌ Não foi possível gerar o post após 3 tentativas em todos os modelos.")


def post_to_linkedin(text: str) -> dict:
    """Publica o texto no LinkedIn via API."""
    url     = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization":             f"Bearer {LINKEDIN_TOKEN}",
        "Content-Type":              "application/json",
        "LinkedIn-Version":          "202210",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    payload = {
        "author":         f"urn:li:person:{LINKEDIN_URN}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary":    {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def should_post() -> bool:
    """Evita postar em commits de CI/automação."""
    skip_keywords = ["[skip linkedin]", "[ci skip]", "chore:", "docs:", "fix typo"]
    msg_lower = COMMIT_MSG.lower()
    return not any(kw in msg_lower for kw in skip_keywords)


def main():
    print(f"📌 Repositório : {REPO_NAME}")
    print(f"📝 Commit      : {COMMIT_MSG}")
    print(f"🌿 Branch      : {BRANCH}")

    if not should_post():
        print("⏭️  Commit marcado para pular. Nenhum post gerado.")
        sys.exit(0)

    print("\n🤖 Gerando post com Gemini...")
    changed_files = get_changed_files()
    post_text = generate_post_with_gemini(COMMIT_MSG, REPO_NAME, changed_files)

    print("\n── Conteúdo gerado ──────────────────────────────────")
    print(post_text)
    print("─────────────────────────────────────────────────────\n")

    print("🚀 Publicando no LinkedIn...")
    result = post_to_linkedin(post_text)
    post_id = result.get("id", "desconhecido")
    print(f"✅ Post publicado com sucesso! ID: {post_id}")


if __name__ == "__main__":
