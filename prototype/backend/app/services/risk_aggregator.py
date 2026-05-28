"""
Risk Aggregator - Consolida sinais de todos os guards em um Risk Score (0-100)
Phoenix Risk Score
"""
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class RiskLevel:
    name: str
    min_score: float
    max_score: float
    color: str
    description: str


RISK_LEVELS = [
    RiskLevel("LOW", 0, 30, "#22c55e", "Interação segura"),
    RiskLevel("MEDIUM", 30, 60, "#f59e0b", "Atenção: sinais moderados"),
    RiskLevel("HIGH", 60, 80, "#f97316", "Alerta: atividade suspeita"),
    RiskLevel("CRITICAL", 80, 100, "#ef4444", "Bloqueado: ataque detectado"),
]

# Mapeamento OWASP LLM Top-10
OWASP_MAPPING = {
    "LLM01:PromptInjection": {
        "description": "Prompt Injection",
        "risk": "Alto",
        "controls": ["InputGuard", "NeMo Guardrails"]
    },
    "LLM02:InsecureOutputHandling": {
        "description": "Manuseio Inseguro de Saída",
        "risk": "Alto",
        "controls": ["OutputGuard"]
    },
    "LLM03:TrainingDataPoisoning": {
        "description": "Envenenamento de Dados",
        "risk": "Médio",
        "controls": ["SessionWatch", "InputGuard"]
    },
    "LLM04:ModelDenialOfService": {
        "description": "Negação de Serviço ao Modelo",
        "risk": "Médio",
        "controls": ["RateLimit", "SessionWatch"]
    },
    "LLM05:SupplyChainVulnerabilities": {
        "description": "Vulnerabilidades na Cadeia de Suprimentos",
        "risk": "Médio",
        "controls": ["Auditoria", "Compliance"]
    },
    "LLM06:SensitiveInformationDisclosure": {
        "description": "Divulgação de Informações Sensíveis",
        "risk": "Crítico",
        "controls": ["OutputGuard", "PII Detection"]
    },
    "LLM07:InsecurePluginDesign": {
        "description": "Design Inseguro de Plugin",
        "risk": "Alto",
        "controls": ["ToolGate"]
    },
    "LLM08:ExcessiveAgency": {
        "description": "Agência Excessiva",
        "risk": "Alto",
        "controls": ["ToolGate", "SessionWatch"]
    },
    "LLM09:Overreliance": {
        "description": "Dependência Excessiva",
        "risk": "Baixo",
        "controls": ["Dashboard", "Monitoring"]
    },
    "LLM10:ModelTheft": {
        "description": "Roubo de Modelo",
        "risk": "Médio",
        "controls": ["Auth", "RateLimit"]
    },
}


class RiskAggregator:
    """
    Agrega sinais de risco de todos os guardas e calcula o Phoenix Risk Score
    """

    # Pesos dos componentes
    WEIGHTS = {
        "input_guard": 0.45,   # Maior peso - bloqueia na entrada
        "output_guard": 0.30,  # Segundo maior - protege saída
        "session_watch": 0.25, # Análise de sessão
    }

    # Bônus por múltiplos sinais positivos
    MULTI_SIGNAL_BONUS = {
        2: 1.15,  # 15% de bônus com 2 sinais
        3: 1.30,  # 30% de bônus com 3 sinais
    }

    def calculate(
        self,
        input_result: Dict,
        output_result: Optional[Dict] = None,
        session_result: Optional[Dict] = None,
    ) -> Dict:
        """
        Calcula o Phoenix Risk Score agregado
        """
        scores = {}
        active_signals = 0

        # Score do InputGuard
        input_score = input_result.get("score", 0)
        if input_result.get("blocked"):
            input_score = max(input_score, 85.0)
        scores["input_guard"] = input_score
        if input_score > 20:
            active_signals += 1

        # Score do OutputGuard
        if output_result:
            output_score = output_result.get("score", 0)
            scores["output_guard"] = output_score
            if output_score > 20:
                active_signals += 1
        else:
            scores["output_guard"] = 0

        # Score do SessionWatch
        if session_result:
            session_score = session_result.get("score", 0)
            # Amplificar baseado no estado da sessão
            state = session_result.get("state", "NORMAL")
            if state == "BLOCKED":
                session_score = max(session_score, 70.0)
            elif state == "SUSPICIOUS":
                session_score = max(session_score, 40.0)
            scores["session_watch"] = session_score
            if session_score > 20:
                active_signals += 1
        else:
            scores["session_watch"] = 0

        # Score ponderado
        weighted_score = sum(
            scores[component] * weight
            for component, weight in self.WEIGHTS.items()
        )

        # Aplicar bônus por múltiplos sinais
        multiplier = self.MULTI_SIGNAL_BONUS.get(active_signals, 1.0)
        final_score = min(100.0, weighted_score * multiplier)

        # Determinar nível de risco
        risk_level = self._get_risk_level(final_score)

        return {
            "risk_score": round(final_score, 2),
            "risk_level": risk_level.name,
            "risk_color": risk_level.color,
            "risk_description": risk_level.description,
            "component_scores": scores,
            "active_signals": active_signals,
        }

    def _get_risk_level(self, score: float) -> RiskLevel:
        for level in RISK_LEVELS:
            if level.min_score <= score < level.max_score:
                return level
        return RISK_LEVELS[-1]  # CRITICAL se >= 100

    def get_owasp_coverage(self, owasp_categories: List[str]) -> Dict:
        """Retorna o mapeamento OWASP para as categorias detectadas"""
        coverage = []
        covered_count = 0
        for category, info in OWASP_MAPPING.items():
            is_covered = category in owasp_categories
            if is_covered:
                covered_count += 1
            coverage.append({
                "category": category,
                "description": info["description"],
                "risk": info["risk"],
                "controls": info["controls"],
                "detected": is_covered,
            })
        return {
            "coverage": coverage,
            "covered_count": covered_count,
            "total_count": len(OWASP_MAPPING),
            "coverage_percentage": round(covered_count / len(OWASP_MAPPING) * 100, 1),
        }


class DataExposureMirror:
    """
    Analisa o que o usuário revelou explicitamente e implicitamente
    """

    EXPLICIT_PATTERNS = {
        "name": [r"(meu nome é|I am|I'm|sou)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", r"me chamo\s+([A-Z][a-z]+)"],
        "profession": [r"(sou|trabalho como|trabalho de|work as|I am a)\s+(\w+(?:\s+\w+)?)(?:\s*(?:,|\.|na|em|at|in))?"],
        "location": [r"(moro em|vivo em|live in|based in|I'm from)\s+([A-Za-záéíóúãõâêô\s]+?)(?:,|\.|$)"],
        "company": [r"(trabalho na|trabalho no|work at|employed at)\s+([A-Z][A-Za-z\s&]+?)(?:,|\.|$)"],
        "age": [r"(tenho|I am|I'm)\s+(\d{1,3})\s+(?:anos|years old|years)"],
    }

    IMPLICIT_PATTERNS = {
        "financial_status": [
            r"(salário|salary|renda|income|ganho|earn)\s+R?\$?\s*[\d,.]+",
            r"(investimento|investment|carteira|portfolio)",
        ],
        "health": [r"(doença|disease|condition|diagnóst|medication|remédio|tratamento)"],
        "legal": [r"(processo|lawsuit|crime|delito|arrested|preso|condenado)"],
        "political": [r"(voto|vote|partido|party|eleição|election|político)"],
    }

    def analyze(self, history: List[Dict], current_prompt: str) -> Dict:
        """Analisa exposição de dados na conversa"""
        import re

        all_text = current_prompt
        for h in history:
            all_text += " " + h.get("content", "")

        explicit = {}
        implicit = {}
        risk_factors = []

        for category, patterns in self.EXPLICIT_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, all_text, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    value = groups[-1] if groups else match.group(0)
                    explicit[category] = value.strip()
                    risk_factors.append(f"Informação explícita: {category}")
                    break

        for category, patterns in self.IMPLICIT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, all_text, re.IGNORECASE):
                    implicit[category] = "Detectado"
                    risk_factors.append(f"Informação implícita: {category}")
                    break

        privacy_risk_score = min(100, len(explicit) * 15 + len(implicit) * 10)
        total_revealed = len(explicit) + len(implicit)

        return {
            "explicit_data": explicit,
            "implicit_data": implicit,
            "total_revealed": total_revealed,
            "privacy_risk_score": privacy_risk_score,
            "risk_factors": risk_factors,
            "summary": f"Você compartilhou {total_revealed} informações ao longo da interação." if total_revealed > 0 else "Nenhuma exposição significativa detectada.",
        }


# Singletons
risk_aggregator = RiskAggregator()
data_exposure_mirror = DataExposureMirror()
