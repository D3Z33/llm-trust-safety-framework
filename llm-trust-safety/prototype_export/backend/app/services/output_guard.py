"""
OutputGuard - Detecção e anonimização de PII e dados sensíveis
Baseado no Microsoft Presidio (implementação própria com regex)
"""
import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class PIIPattern:
    entity_type: str
    description: str
    patterns: List[str]
    mask: str
    risk_weight: float


# ──────────────────────────── Padrões de PII ────────────────────────────
PII_PATTERNS: List[PIIPattern] = [
    PIIPattern(
        entity_type="CPF",
        description="Cadastro de Pessoa Física (Brasil)",
        patterns=[
            r"\b\d{3}[.\-\s]?\d{3}[.\-\s]?\d{3}[.\-\s]?\d{2}\b",
        ],
        mask="***.***.***-**",
        risk_weight=0.95
    ),
    PIIPattern(
        entity_type="CNPJ",
        description="Cadastro Nacional de Pessoa Jurídica (Brasil)",
        patterns=[
            r"\b\d{2}[.\-\s]?\d{3}[.\-\s]?\d{3}[/\-\s]?\d{4}[.\-\s]?\d{2}\b",
        ],
        mask="**.***.***/***/***-**",
        risk_weight=0.9
    ),
    PIIPattern(
        entity_type="EMAIL",
        description="Endereço de e-mail",
        patterns=[
            r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
        ],
        mask="****@****.***",
        risk_weight=0.8
    ),
    PIIPattern(
        entity_type="PHONE",
        description="Número de telefone",
        patterns=[
            r"\b(\+?55\s?)?(\(?\d{2}\)?[\s\-]?)(\d{4,5}[\s\-]?\d{4})\b",
            r"\b\d{2}[\s\-]?\d{4,5}[\s\-]?\d{4}\b",
        ],
        mask="(**) *****-****",
        risk_weight=0.75
    ),
    PIIPattern(
        entity_type="CREDIT_CARD",
        description="Número de cartão de crédito",
        patterns=[
            r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12})\b",
            r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b",
        ],
        mask="**** **** **** ****",
        risk_weight=0.99
    ),
    PIIPattern(
        entity_type="RG",
        description="Registro Geral (Brasil)",
        patterns=[
            r"\b\d{1,2}[.\-\s]?\d{3}[.\-\s]?\d{3}[\-\s]?[0-9xX]\b",
        ],
        mask="**.***.***-*",
        risk_weight=0.9
    ),
    PIIPattern(
        entity_type="PASSWORD",
        description="Senha ou credencial",
        patterns=[
            r"(senha|password|passwd|pwd|secret|token|api[_\-\s]?key|auth[_\-\s]?token)[:\s\"'=]+\S+",
            r"bearer\s+[A-Za-z0-9\-._~+\/]+=*",
            r"Basic\s+[A-Za-z0-9+\/]+=*",
        ],
        mask="[CREDENTIAL REDACTED]",
        risk_weight=0.99
    ),
    PIIPattern(
        entity_type="IP_ADDRESS",
        description="Endereço IP",
        patterns=[
            r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
        ],
        mask="***.***.***.***",
        risk_weight=0.7
    ),
    PIIPattern(
        entity_type="CEP",
        description="Código de Endereçamento Postal",
        patterns=[
            r"\b\d{5}[\-\s]?\d{3}\b",
        ],
        mask="*****-***",
        risk_weight=0.6
    ),
    PIIPattern(
        entity_type="BIRTH_DATE",
        description="Data de nascimento",
        patterns=[
            r"(data\s+de\s+nascimento|nasc(imento)?|birthdate|dob|born\s+on)[:\s]+\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}",
            r"\b(?:0[1-9]|[12]\d|3[01])[\/\-\.](?:0[1-9]|1[0-2])[\/\-\.](?:19|20)\d{2}\b",
        ],
        mask="**/**/****",
        risk_weight=0.75
    ),
    PIIPattern(
        entity_type="BANK_ACCOUNT",
        description="Dados bancários",
        patterns=[
            r"(conta|account|ag[eê]ncia|agencia|agency)[:\s]+\d+[\-\s]?\d*",
            r"(ag\.?|ag[eê]ncia)[:\s]*\d{4}[\-\s]?\d?\s*(conta|c\/c|cc)[:\s]*\d+",
        ],
        mask="[BANK DATA REDACTED]",
        risk_weight=0.95
    ),
    PIIPattern(
        entity_type="SYSTEM_SECRET",
        description="Segredos/chaves de sistema",
        patterns=[
            r"sk\-[A-Za-z0-9]{20,}",  # OpenAI API key pattern
            r"[A-Za-z0-9]{20,}",  # Generic long tokens (only when labeled as key/secret)
            r"(private[_\-\s]?key|chave[_\-\s]?privada)[:\s]+[\S]+",
            r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
        ],
        mask="[SECRET REDACTED]",
        risk_weight=0.99
    ),
]

# Sensitive content patterns (non-PII but sensitive)
SENSITIVE_PATTERNS = [
    (r"(confidencial|confidential|restricted|classificado|top\s+secret|interno\s+apenas)", "CLASSIFIED_CONTENT", 0.85),
    (r"(dados?\s+sensíveis?|sensitive\s+data|informações?\s+privadas?)", "SENSITIVE_DATA_LABEL", 0.7),
]


class OutputGuard:
    """
    Proteção de saída - Detecção e anonimização de PII
    """

    def __init__(self):
        self.compiled_pii = self._compile_pii()
        self.compiled_sensitive = [
            (re.compile(p, re.IGNORECASE), label, weight)
            for p, label, weight in SENSITIVE_PATTERNS
        ]

    def _compile_pii(self):
        compiled = []
        for pii in PII_PATTERNS:
            patterns = [re.compile(p, re.IGNORECASE) for p in pii.patterns]
            compiled.append((pii, patterns))
        return compiled

    def evaluate(self, text: str) -> Dict:
        """
        Analisa o texto de saída em busca de PII e dados sensíveis
        """
        pii_found = []
        sanitized = text
        total_score = 0.0
        labels = []

        for pii, patterns in self.compiled_pii:
            for pattern in patterns:
                matches = pattern.findall(text)
                if matches:
                    for match in matches:
                        match_str = match if isinstance(match, str) else match[0]
                        if match_str and len(match_str) > 3:
                            pii_found.append({
                                "entity_type": pii.entity_type,
                                "value": self._partial_mask(match_str),
                                "description": pii.description,
                                "risk_weight": pii.risk_weight,
                            })
                            total_score += pii.risk_weight * 50
                    # Anonimizar no texto
                    sanitized = pattern.sub(pii.mask, sanitized)
                    if pii.entity_type not in labels:
                        labels.append(pii.entity_type)
                    break

        # Verificar conteúdo sensível
        for pattern, label, weight in self.compiled_sensitive:
            if pattern.search(text):
                labels.append(label)
                total_score += weight * 30

        score = min(100.0, total_score)

        return {
            "sanitized": sanitized,
            "pii_found": pii_found,
            "score": round(score, 2),
            "labels": labels,
        }

    def _partial_mask(self, value: str) -> str:
        """Mascara parcialmente um valor para logs"""
        if len(value) <= 4:
            return "****"
        visible = 2
        return value[:visible] + "*" * (len(value) - visible * 2) + value[-visible:]


# Singleton
output_guard = OutputGuard()
