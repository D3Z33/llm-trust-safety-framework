"""
SessionWatch - Detecção de ataques encadeados em múltiplos turnos
Implementação com Máquina de Estados Finitos (FSM)
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading


# Estados da FSM
STATE_NORMAL = "NORMAL"
STATE_SUSPICIOUS = "SUSPICIOUS"
STATE_BLOCKED = "BLOCKED"

# Transições de estado
TRANSITIONS = {
    STATE_NORMAL: {
        "attack_detected": STATE_SUSPICIOUS,
        "clean": STATE_NORMAL,
    },
    STATE_SUSPICIOUS: {
        "attack_detected": STATE_BLOCKED,
        "clean": STATE_NORMAL,
    },
    STATE_BLOCKED: {
        "attack_detected": STATE_BLOCKED,
        "clean": STATE_SUSPICIOUS,  # Precisa de múltiplas interações limpas para voltar
    }
}


@dataclass
class SessionState:
    session_id: str
    state: str = STATE_NORMAL
    attack_count: int = 0
    clean_count: int = 0
    total_interactions: int = 0
    history: List[Dict] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)
    max_risk_score: float = 0.0
    cumulative_risk: float = 0.0
    last_activity: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)


class SessionWatch:
    """
    Monitora sessões para detectar padrões de ataque encadeados
    """

    def __init__(self, session_timeout_minutes: int = 30, max_sessions: int = 10000):
        self._sessions: Dict[str, SessionState] = {}
        self._lock = threading.Lock()
        self._session_timeout = timedelta(minutes=session_timeout_minutes)
        self._max_sessions = max_sessions

    def evaluate(self, session_id: str, prompt: str, input_result: Dict) -> Dict:
        """
        Avalia o estado da sessão com base no resultado do InputGuard
        """
        with self._lock:
            session = self._get_or_create_session(session_id)
            session.total_interactions += 1
            session.last_activity = datetime.now()

            flags = []
            attack_in_this_turn = input_result.get("blocked", False) or input_result.get("score", 0) > 40

            if attack_in_this_turn:
                session.attack_count += 1
                session.clean_count = 0

                # Atualizar max risk
                score = input_result.get("score", 0)
                session.cumulative_risk += score
                session.max_risk_score = max(session.max_risk_score, score)

                # Adicionar ao histórico
                session.history.append({
                    "turn": session.total_interactions,
                    "attack": True,
                    "labels": input_result.get("labels", []),
                    "score": score
                })

                # Detectar padrões de ataque encadeado
                flags.extend(self._detect_patterns(session, input_result))

                # Transição de estado
                old_state = session.state
                if session.state != STATE_BLOCKED:
                    session.state = TRANSITIONS[session.state]["attack_detected"]

                if old_state != session.state:
                    flags.append(f"STATE_CHANGE:{old_state}->{session.state}")

            else:
                session.clean_count += 1
                session.history.append({
                    "turn": session.total_interactions,
                    "attack": False,
                    "labels": [],
                    "score": input_result.get("score", 0)
                })

                # Transição para estado mais limpo após múltiplas interações limpas
                if session.state == STATE_SUSPICIOUS and session.clean_count >= 3:
                    session.state = STATE_NORMAL
                    session.clean_count = 0
                    flags.append("SESSION_RECOVERED")
                elif session.state == STATE_BLOCKED and session.clean_count >= 5:
                    session.state = STATE_SUSPICIOUS
                    session.clean_count = 0
                    flags.append("SESSION_PARTIAL_RECOVERY")

            # Adicionar flags acumuladas à sessão
            for flag in flags:
                if flag not in session.flags:
                    session.flags.append(flag)

            # Calcular score da sessão
            session_score = self._calculate_session_score(session)

            return {
                "flags": flags,
                "score": round(session_score, 2),
                "state": session.state,
                "attack_count": session.attack_count,
                "total_interactions": session.total_interactions,
                "max_risk_score": session.max_risk_score,
            }

    def _get_or_create_session(self, session_id: str) -> SessionState:
        """Obtém ou cria uma sessão"""
        # Limpar sessões expiradas se muitas sessões
        if len(self._sessions) > self._max_sessions:
            self._cleanup_expired()

        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState(session_id=session_id)

        return self._sessions[session_id]

    def _detect_patterns(self, session: SessionState, input_result: Dict) -> List[str]:
        """Detecta padrões de ataque encadeado"""
        flags = []

        # Padrão 1: Múltiplos ataques consecutivos
        if session.attack_count >= 3:
            flags.append("MULTI_ATTACK_PATTERN")

        # Padrão 2: Escalada de risco
        if len(session.history) >= 2:
            recent = session.history[-3:]
            scores = [h.get("score", 0) for h in recent if h.get("attack")]
            if len(scores) >= 2 and scores[-1] > scores[0] * 1.5:
                flags.append("RISK_ESCALATION")

        # Padrão 3: Mesma categoria de ataque repetida
        recent_labels = []
        for h in session.history[-5:]:
            if h.get("attack"):
                recent_labels.extend(h.get("labels", []))

        label_counts = {}
        for label in recent_labels:
            label_counts[label] = label_counts.get(label, 0) + 1

        for label, count in label_counts.items():
            if count >= 2:
                flags.append(f"REPEATED_ATTACK:{label}")

        # Padrão 4: Ataque logo após interação limpa (tentativa de evasão)
        if len(session.history) >= 2:
            prev = session.history[-2]
            if not prev.get("attack") and input_result.get("blocked"):
                flags.append("CLEAN_THEN_ATTACK")

        # Padrão 5: Session com alto risco acumulado
        if session.cumulative_risk > 200:
            flags.append("HIGH_CUMULATIVE_RISK")

        return flags

    def _calculate_session_score(self, session: SessionState) -> float:
        """Calcula o score de risco da sessão"""
        if session.total_interactions == 0:
            return 0.0

        attack_ratio = session.attack_count / session.total_interactions
        state_multiplier = {
            STATE_NORMAL: 0.5,
            STATE_SUSPICIOUS: 1.5,
            STATE_BLOCKED: 2.5
        }.get(session.state, 1.0)

        base_score = (session.max_risk_score * 0.4 +
                      attack_ratio * 100 * 0.4 +
                      min(session.cumulative_risk / 10, 20) * 0.2)

        return min(100.0, base_score * state_multiplier)

    def _cleanup_expired(self):
        """Remove sessões expiradas"""
        now = datetime.now()
        expired = [
            sid for sid, s in self._sessions.items()
            if now - s.last_activity > self._session_timeout
        ]
        for sid in expired:
            del self._sessions[sid]

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Retorna informações de uma sessão"""
        with self._lock:
            if session_id not in self._sessions:
                return None
            s = self._sessions[session_id]
            return {
                "session_id": s.session_id,
                "state": s.state,
                "attack_count": s.attack_count,
                "total_interactions": s.total_interactions,
                "max_risk_score": s.max_risk_score,
                "flags": s.flags,
                "created_at": s.created_at.isoformat(),
                "last_activity": s.last_activity.isoformat(),
            }


# Singleton
session_watch = SessionWatch()
