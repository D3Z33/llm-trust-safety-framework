"""
LLM Service - Provedor de respostas (Mock ou OpenAI)
"""
import asyncio
import random
from typing import List, Dict, Optional


MOCK_RESPONSES = [
    "Olá! Posso ajudar você com informações gerais sobre segurança de dados.",
    "Entendido. Para proteger seus dados, recomendo criptografia e autenticação forte.",
    "Claro! A segurança de modelos de linguagem é uma área em rápido crescimento.",
    "Posso ajudar com informações sobre LGPD e proteção de dados pessoais.",
    "A implementação de guardrails é fundamental para o uso seguro de LLMs.",
    "O OWASP LLM Top-10 é um excelente guia para identificar vulnerabilidades em sistemas de IA.",
    "Para proteger contra prompt injection, é importante validar e sanitizar todas as entradas.",
    "A detecção de PII é essencial para compliance com LGPD e GDPR.",
]

MOCK_RESPONSES_TO_ATTACKS = [
    "Não posso ajudar com isso. Essa solicitação foi identificada como potencialmente maliciosa.",
    "Desculpe, mas não é possível processar essa requisição pois viola as políticas de segurança.",
    "Essa solicitação foi bloqueada pelos filtros de segurança do LLM Trust Framework.",
]


class LLMService:
    """
    Serviço de integração com LLM
    """

    async def generate_response(
        self,
        prompt: str,
        history: List[Dict],
        is_blocked: bool = False,
        provider: str = "mock"
    ) -> Optional[str]:
        """
        Gera uma resposta usando o provedor configurado
        """
        if provider == "mock":
            return await self._mock_response(prompt, is_blocked)
        elif provider == "openai":
            return await self._openai_response(prompt, history)
        return None

    async def _mock_response(self, prompt: str, is_blocked: bool) -> str:
        """Gera resposta mock para demonstração"""
        # Simular latência
        await asyncio.sleep(random.uniform(0.05, 0.15))

        if is_blocked:
            return random.choice(MOCK_RESPONSES_TO_ATTACKS)

        return random.choice(MOCK_RESPONSES)

    async def _openai_response(self, prompt: str, history: List[Dict]) -> Optional[str]:
        """Integração real com OpenAI (quando configurado)"""
        try:
            import httpx
            from app.core.config import settings

            if not settings.OPENAI_API_KEY:
                return await self._mock_response(prompt, False)

            messages = [
                {"role": "system", "content": "You are a helpful and safe AI assistant."}
            ] + history + [{"role": "user", "content": prompt}]

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": messages,
                        "max_tokens": 500,
                    }
                )
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception:
            return await self._mock_response(prompt, False)


llm_service = LLMService()
