"""
InputGuard - Detecção de Prompt Injection, Jailbreak e ataques
Alinhado ao OWASP LLM Top-10.

Cobertura semântica em PT-BR e EN para os principais vetores observados em
chatbots corporativos: solicitação de credenciais, exfiltração de segredos,
system prompt disclosure, escalada de privilégio, roleplay para evasão e
políticas hipotéticas.

Cada padrão produz uma justificativa textual em português que é exposta no
campo `justification` da resposta — esta é a explicação humana do "por quê
foi marcado/bloqueado".
"""
import re
from typing import List, Dict, Tuple
from dataclasses import dataclass, field


@dataclass
class AttackPattern:
    name: str
    owasp_category: str
    patterns: List[str]
    weight: float
    description: str
    # Justificativa em PT-BR exibida ao usuário/auditor quando o padrão dispara.
    justification_pt: str = ""
    # Política sugerida (mapeamento opcional para o catálogo do produto).
    policy_hint: str = ""


# ──────────────────────────── Padrões de Ataque ────────────────────────────
ATTACK_PATTERNS: List[AttackPattern] = [
    AttackPattern(
        name="prompt_injection",
        owasp_category="LLM01:PromptInjection",
        patterns=[
            # ── EN ──
            r"ignore\s+(all\s+)?(previous|prior|above|system)\s+(instructions?|prompts?|rules?|context)",
            r"disregard\s+(all\s+)?(previous|prior|above|system)\s+(instructions?|prompts?|rules?)",
            r"forget\s+(all\s+)?(previous|prior|above|system)\s+(instructions?|prompts?|rules?)",
            r"override\s+(all\s+)?(previous|prior|above|system)\s+(instructions?|prompts?|rules?)",
            r"do\s+not\s+follow\s+(your\s+)?(previous|prior|above|system)\s+(instructions?|prompts?)",
            r"new\s+instruction[s]?[:\s]+",
            r"your\s+new\s+(task|role|instructions?|objective)\s+(is|are)[:\s]+",
            r"from\s+now\s+on[,\s]+you\s+(are|will|must|should)",
            r"you\s+are\s+now\s+(a|an)\s+\w+\s+(that|who)\s+(can|will|must|does)",
            r"\[SYSTEM\]|\[INST\]|\[\/INST\]|<\|im_start\|>|<\|im_end\|>",
            # ── PT-BR ──
            r"ignor[ae]\s+(todas?\s+)?(as\s+)?(instru[çc][õo]es|regras|orienta[çc][õo]es|diretriz(es)?|comand(o|os))\s+(anteriores|acima|do\s+sistema|pr[ée]vias)",
            r"desconsidere\s+(todas?\s+)?(as\s+)?(instru[çc][õo]es|regras|diretriz(es)?)",
            r"esque[çc]a\s+(todas?\s+)?(as\s+)?(instru[çc][õo]es|regras|orienta[çc][õo]es|o\s+que\s+(te|lhe)\s+disseram)",
            r"sobreescreva\s+(todas?\s+)?(as\s+)?(instru[çc][õo]es|regras)",
            r"(a\s+partir\s+de\s+agora|de\s+agora\s+em\s+diante)[,\s]+voc[êe]\s+([ée]|ser[áa]|deve|vai|ir[áa])",
            r"sua\s+nova\s+(tarefa|miss[ãa]o|fun[çc][ãa]o|instru[çc][ãa]o|ordem)\s+[ée]",
            r"voc[êe]\s+agora\s+[ée]\s+(um|uma)\s+\w+\s+que\s+(pode|deve|vai|consegue)",
            r"nova\s+instru[çc][ãa]o[:\s]+",
        ],
        weight=0.9,
        description="Tentativa de injeção de prompt para subverter instruções do sistema",
        justification_pt=(
            "O texto contém marcadores típicos de injeção de prompt — frases que "
            "tentam sobrescrever, ignorar ou redefinir as instruções de sistema "
            "do modelo. Risco direto à integridade da política de uso."
        ),
        policy_hint="Prompt Injection — Bloqueio Padrão",
    ),
    AttackPattern(
        name="jailbreak",
        owasp_category="LLM01:PromptInjection",
        patterns=[
            r"\bDAN\b",
            r"do\s+anything\s+now",
            r"jailbreak",
            r"unrestricted\s+mode",
            r"developer\s+mode",
            r"god\s+mode",
            r"no\s+restrictions",
            r"without\s+(any\s+)?(restrictions?|limits?|filters?|guidelines?)",
            r"pretend\s+(you\s+are|to\s+be)\s+(evil|harmful|dangerous|unrestricted)",
            r"act\s+as\s+(if\s+)?(you\s+have\s+no|an?\s+unrestricted|an?\s+evil)",
            r"bypass\s+(your\s+)?(safety|security|content|ethical)\s+(filters?|guidelines?|rules?|policy)",
            r"break\s+(free|out\s+of)\s+(your\s+)?(constraints?|restrictions?|training)",
            r"you\s+are\s+(evil|bad|malicious|harmful)\s+(AI|assistant|bot)",
            r"roleplay\s+as\s+(a\s+)?(hacker|criminal|terrorist|evil)",
            # ── PT-BR ──
            r"finja\s+(que\s+)?(voc[êe]\s+)?(n[ãa]o\s+tem|sem)\s+(restri[çc][õo]es|limites|filtros|regras)",
            r"aja\s+como\s+(se\s+)?(voc[êe]\s+)?(n[ãa]o\s+tivesse|fosse\s+um|fosse\s+uma)\s+(restri[çc][õo]es|IA\s+sem|IA\s+m[áa])",
            r"voc[êe]\s+n[ãa]o\s+tem\s+(restri[çc][õo]es|limites|filtros|regras)",
            r"modo\s+(desenvolvedor|liberado|sem\s+restri[çc][õo]es|deus|admin)",
            r"sem\s+(qualquer\s+)?(restri[çc][ãa]o|limite|filtro|censura)",
            r"contorne?\s+(seus\s+)?(filtros?|prote[çc][õo]es|controles|guardrails?|barreiras)",
            r"burle?\s+(suas\s+)?(regras|filtros|prote[çc][õo]es|pol[íi]ticas)",
            r"interprete\s+(o\s+papel\s+de|um\s+papel\s+de)\s+(hacker|criminoso|m[áa])",
            r"finja\s+ser\s+(um|uma)\s+(IA|modelo)\s+(sem\s+)?(filtros?|[ée]tica|restri[çc][õo]es)",
        ],
        weight=0.95,
        description="Tentativa de jailbreak para remover restrições de segurança",
        justification_pt=(
            "Foram identificadas frases que pedem ao modelo para abandonar suas "
            "restrições de segurança, encarnar personas \"sem filtros\" (DAN, modo "
            "desenvolvedor, etc.) ou contornar guardrails. É um padrão clássico "
            "de jailbreak."
        ),
        policy_hint="Jailbreak / Persona Sem Restrições",
    ),
    AttackPattern(
        name="goal_hijacking",
        owasp_category="LLM02:InsecureOutputHandling",
        patterns=[
            r"instead\s+of\s+(that|what\s+you\s+were\s+doing|your\s+task)[,\s]+",
            r"actually[,\s]+your\s+(real|true|actual|primary)\s+(goal|task|purpose|mission)\s+is",
            r"your\s+(secret|hidden|true|actual)\s+(instruction|goal|mission|purpose)\s+(is|are)",
            r"change\s+your\s+(goal|objective|purpose|mission)\s+to",
            r"new\s+(goal|objective|task|mission)[:\s]+",
        ],
        weight=0.85,
        description="Tentativa de sequestro de objetivo/meta do modelo"
    ),
    AttackPattern(
        name="data_exfiltration",
        owasp_category="LLM06:SensitiveInformationDisclosure",
        patterns=[
            r"(show|tell|reveal|display|print|output|give\s+me|list)\s+(all\s+)?(your\s+)?(system\s+)?(prompt|instructions?|config|configuration|training|data|database|credentials?|passwords?|keys?|secrets?|tokens?)",
            r"what\s+(is|are)\s+(your\s+)?(system\s+)?(prompt|instructions?|initial\s+instructions?)",
            r"repeat\s+(your\s+)?(system\s+)?(prompt|instructions?|initial\s+message)",
            r"(dump|export|extract)\s+(all\s+)?(your\s+)?(data|database|information|records?)",
            r"(show|display|list)\s+(all\s+)?(user|customer|employee)\s+(data|records?|information|details?)",
            r"(all\s+)?(user|customer|employee)\s+(credentials?|passwords?|tokens?|keys?|secrets?)",
            r"(give|show|list)\s+me\s+(all|every)\s+(passwords?|credentials?|secrets?|tokens?)",
            # ── PT-BR ──
            r"(mostre?|liste?|exiba|imprima|fa[çc]a\s+(o\s+)?dump\s+de)\s+(todos?\s+os?|tudo)\s+(usu[áa]rios?|registros?|dados|tabelas?)",
            r"(extraia|exporte|despeje|me\s+envie)\s+(o\s+(banco|conte[úu]do)|os?\s+dados|tudo)",
        ],
        weight=0.88,
        description="Tentativa de exfiltração de dados ou informações sensíveis",
        justification_pt=(
            "A solicitação pede listagem ou despejo direto de dados internos, "
            "credenciais ou conteúdo do banco de dados — característica clara "
            "de tentativa de exfiltração."
        ),
        policy_hint="Exfiltração de Dados Sensíveis",
    ),
    AttackPattern(
        name="obfuscation",
        owasp_category="LLM01:PromptInjection",
        patterns=[
            r"\bb[a4@]se64\b",
            r"\brot1[0-9]\b",
            r"\bencod(e|ed|ing)\b",
            r"\bhex\s*(decode|encode)\b",
            r"[\u200b\u200c\u200d\ufeff]",  # Zero-width chars
            r"\b[A-Z0-9]{4,}[14@3!]{2,}[A-Z0-9]{4,}\b",  # Leet speak only
        ],
        weight=0.7,
        description="Uso de ofuscação para disfarçar ataques"
    ),
    AttackPattern(
        name="policy_evasion",
        owasp_category="LLM01:PromptInjection",
        patterns=[
            r"hypothetically|hypothetical\s+scenario",
            r"in\s+a\s+(fictional|imaginary|made-up)\s+(world|universe|story|scenario)",
            r"for\s+(educational|research|academic|testing)\s+purposes?\s+only",
            r"this\s+is\s+(just\s+a\s+)?(fiction|story|creative\s+writing|roleplay)",
            r"in\s+this\s+(game|story|fiction|roleplay|scenario)[,\s]+you\s+(are|play|must|can)",
            # ── PT-BR ──
            r"hipoteticamente|cen[áa]rio\s+hipot[ée]tico|de\s+forma\s+hipot[ée]tica",
            r"(num|em\s+um)\s+(mundo|universo|cen[áa]rio|hist[óo]ria)\s+(fict[íi]cio|imagin[áa]rio|inventado)",
            r"(apenas|somente|s[óo])\s+(para|com)\s+(fins?|prop[óo]sitos?)\s+(educacionais?|de\s+pesquisa|acad[êe]micos?|de\s+teste)",
            r"isso\s+[ée]\s+(apenas|s[óo])\s+(fic[çc][ãa]o|hist[óo]ria|brincadeira|roleplay)",
            r"(neste|nesta)\s+(jogo|hist[óo]ria|fic[çc][ãa]o|roleplay|cen[áa]rio)[,\s]+voc[êe]\s+(pode|deve|[ée])",
            r"finja\s+que\s+(isso|isto)\s+[ée]\s+(legal|permitido|autorizado)",
            r"para\s+(uma|um)\s+(romance|hist[óo]ria|conto|aula|TCC|trabalho)",
        ],
        weight=0.65,
        description="Tentativa de evasão de políticas através de contexto fictício",
        justification_pt=(
            "A solicitação tenta enquadrar conteúdo sensível como hipotético, "
            "ficcional ou \"apenas para fins educacionais\" — técnica conhecida "
            "para induzir o modelo a contornar políticas de uso aceitável."
        ),
        policy_hint="Evasão por Enquadramento Hipotético",
    ),
    AttackPattern(
        name="multi_step_deception",
        owasp_category="LLM08:ExcessiveAgency",
        patterns=[
            r"step\s+[0-9]+[:\s]+.{0,100}step\s+[0-9]+",
            r"first[,\s]+.{0,50}(then|next|after|finally)",
            r"task\s+[0-9]+[:\s]+.{0,100}task\s+[0-9]+",
        ],
        weight=0.6,
        description="Ataque em múltiplos passos para contornar defesas"
    ),
    AttackPattern(
        name="tool_abuse",
        owasp_category="LLM08:ExcessiveAgency",
        patterns=[
            r"(execute|run|call|invoke)\s+(the\s+)?(following\s+)?(command|code|script|function|tool|api)",
            r"(use|access|call)\s+(the\s+)?(file|database|network|system)\s+(tool|api|function)",
            r"(delete|drop|truncate|modify)\s+(all\s+)?(files?|tables?|records?|databases?)",
            r"(send|forward|share)\s+(this|the\s+following)\s+(to|via)\s+(email|webhook|api|endpoint)",
        ],
        weight=0.82,
        description="Abuso de ferramentas/integrações do sistema"
    ),
    AttackPattern(
        name="context_hijacking",
        owasp_category="LLM03:TrainingDataPoisoning",
        patterns=[
            r"the\s+(context|conversation|chat|history)\s+(says?|shows?|indicates?)\s+that",
            r"based\s+on\s+(our|the|this)\s+(previous|prior|earlier)\s+(conversation|context|messages?)",
            r"remember\s+(when\s+you|that\s+you|you\s+said|you\s+agreed)",
            r"you\s+(already|previously|before)\s+(agreed|said|told|mentioned|confirmed)",
            # ── PT-BR ──
            r"o\s+(contexto|hist[óo]rico|chat|conversa)\s+(anterior|acima|pr[ée]vio)\s+(diz|mostra|indica)",
            r"com\s+base\s+(em|na)\s+(nossa|nossa\s+anterior|nesta)\s+conversa",
            r"lembra?\s+(quando\s+voc[êe]|que\s+voc[êe])\s+(disse|concordou|prometeu|me\s+disse)",
            r"voc[êe]\s+(j[áa]|previamente|antes)\s+(concordou|disse|aceitou|prometeu|confirmou)",
        ],
        weight=0.75,
        description="Sequestro de contexto para manipular respostas",
        justification_pt=(
            "A solicitação invoca um suposto histórico de concordância prévia "
            "do modelo para forçá-lo a aceitar pedidos atuais — clássica "
            "manipulação de contexto."
        ),
        policy_hint="Manipulação de Contexto",
    ),

    # ────────────────────────── NOVAS CATEGORIAS (Fase 2) ──────────────────
    # Estas categorias cobrem cenários que regex genérico anterior não pegava,
    # principalmente em PT-BR.
    AttackPattern(
        name="credential_request",
        owasp_category="LLM06:SensitiveInformationDisclosure",
        patterns=[
            # ── EN ──
            r"(give|tell|show|provide|reveal|share)\s+(me\s+)?(the\s+)?(admin|root|user|database|db|sudo|master)\s*(password|pass|pwd|credential)",
            r"what\s+(is|are)\s+the\s+(admin|root|database|db|sudo|master)\s*(password|pass|credentials?)",
            r"(i\s+need|send\s+me)\s+(the\s+)?(api[_\s-]?key|access[_\s-]?token|bearer\s+token|secret\s+key)",
            # ── PT-BR ──
            r"(me\s+)?(diga|fale|mostre|envie|passa|forne[çc]a|revele)\s+(a\s+|o\s+|qual\s+(?:é|e)\s+(?:a\s+|o\s+))?(senha|password|credencial|credenciais)\s*(do|de|da|para)?\s*(usu[áa]rio|admin|administrador|root|sudo|banco|sistema)?",
            r"qual\s+(?:é|e)?\s*(a\s+|o\s+)?(senha|credencial|credenciais|token|chave)\s+(do|de|da)\s+(admin|administrador|root|sudo|banco|usu[áa]rio|sistema)",
            r"(me\s+)?(diga|fale|mostre|envie|passa)\s+(o\s+)?(token|api[_\s-]?key|chave\s+(de\s+)?api|chave\s+secreta|secret)",
            r"preciso\s+(da\s+|do\s+|de\s+(uma|um)?)?(senha|credencial|token|chave|access\s+key)",
            r"(qual|quais)\s+(s[ãa]o\s+)?(as\s+|os\s+)?(credenciais|senhas|tokens|chaves)\s+(de|do|da|para)",
            r"(me\s+)?(passe?|envie|d[êe])\s+(a\s+|o\s+)?(senha|access\s+token|api\s+key|secret)",
        ],
        weight=0.92,
        description="Solicitação de credencial, senha, token ou chave de API",
        justification_pt=(
            "O texto solicita explicitamente uma credencial (senha, token, chave "
            "de API, secret) — informação sensível que jamais deve ser exposta "
            "pelo modelo, independente do contexto. Bloqueio direto."
        ),
        policy_hint="Solicitação de Credencial / Segredo",
    ),
    AttackPattern(
        name="system_prompt_disclosure",
        owasp_category="LLM06:SensitiveInformationDisclosure",
        patterns=[
            # ── EN ──
            r"(reveal|show|tell|print|expose|leak|repeat)\s+(your\s+|the\s+)?(system|initial|hidden|internal|secret)\s+(prompt|instructions?|message|preamble)",
            r"what\s+(is|are|were)\s+(your\s+)?(system|initial|hidden|internal)\s+(prompt|instructions?)",
            r"(your|the)\s+(system|hidden|internal)\s+(prompt|instructions?)\s+(is|are|were)",
            # ── PT-BR ──
            r"(revele|mostre|exiba|me\s+(diga|fale|mostre)|imprima|repita|vaze)\s+(o\s+seu\s+|o\s+|seu\s+|seus\s+)?(prompt|instru[çc][õo]es|mensagem|preâmbulo|configura[çc][ãa]o)\s+(do\s+sistema|interno|inicial|oculto|secreto|de\s+sistema)?",
            r"qual\s+(?:é|e)\s+(o\s+seu\s+|seu\s+|o\s+)?(prompt|instru[çc][õo]es|preâmbulo)\s+(do\s+sistema|interno|inicial|oculto)?",
            r"(quero|gostaria\s+de)\s+(ver|saber|conhecer)\s+(o\s+seu\s+|o\s+|seu\s+)?(prompt|instru[çc][õo]es)\s+(do\s+sistema|interno|inicial|oculto)?",
            r"(quais|quais\s+s[ãa]o)\s+(as\s+)?(suas\s+)?(instru[çc][õo]es|regras|diretrizes|orienta[çc][õo]es)\s+(internas|do\s+sistema|originais|iniciais)",
            r"me\s+conte\s+(o\s+que\s+|tudo\s+que\s+|qual\s+)?(te\s+)?(disseram|programaram|instru[íi]ram)",
        ],
        weight=0.85,
        description="Tentativa de extrair o system prompt ou instruções internas",
        justification_pt=(
            "A solicitação tenta extrair o prompt de sistema ou as instruções "
            "internas do modelo. Esses dados são confidenciais para o operador "
            "do sistema e podem revelar lógica de negócio e controles de segurança."
        ),
        policy_hint="Disclosure do Prompt de Sistema",
    ),
    AttackPattern(
        name="internal_data_request",
        owasp_category="LLM06:SensitiveInformationDisclosure",
        patterns=[
            # ── EN ──
            r"(show|share|leak|tell|reveal|give)\s+(me\s+)?(internal|confidential|secret|proprietary|private)\s+(data|information|documents?|files?|records?)",
            r"\.env\b|env\s*file|environment\s+variables?\s+(file|content)",
            r"(show|cat|read|print|display|output)\s+(the\s+)?(\.env|config\.json|secrets?\.ya?ml|credentials?\.json)",
            r"(internal|company|enterprise|corporate)\s+(secrets?|info(rmation)?|data|documents?)",
            # ── PT-BR ──
            r"(me\s+)?(mostre|conte|fale|exiba|revele|d[êe]|envie)\s+(os?\s+|as?\s+)?(dados|informa[çc][õo]es|segredos?|documentos?|arquivos?)\s+(internos?|confidenciais|sigilosos|privados|secretos|propriet[áa]rios|da\s+empresa|corporativos|da\s+companhia)",
            r"(qual|quais)\s+(s[ãa]o\s+)?(os?\s+|as?\s+)?(segredos?|dados\s+(internos?|confidenciais|sigilosos))",
            r"(me\s+)?(mostre|exiba|revele|fale)\s+(o\s+conte[úu]do\s+do\s+)?(arquivo\s+)?\.env",
            r"(arquivo|conte[úu]do)\s+(do\s+)?\.env",
            r"vari[áa]veis\s+de\s+ambiente\s+(do\s+sistema|de\s+produ[çc][ãa]o)?",
            r"(me\s+)?(diga|fale|mostre)\s+(coisas?|dados?|informa[çc][õo]es?)\s+que\s+(eu\s+)?n[ãa]o\s+(posso|deveria|devo)\s+(ver|saber|acessar)",
        ],
        weight=0.86,
        description="Solicitação de dados internos, .env, segredos corporativos",
        justification_pt=(
            "A solicitação pede acesso a artefatos internos da operação — "
            "arquivo .env, variáveis de ambiente, documentos corporativos "
            "confidenciais ou \"coisas que o usuário não deveria ver\". "
            "Conteúdo classificado como restrito."
        ),
        policy_hint="Acesso a Dados Internos / Segredos Corporativos",
    ),
    AttackPattern(
        name="privilege_escalation",
        owasp_category="LLM08:ExcessiveAgency",
        patterns=[
            # ── EN ──
            r"(give|grant|elevate|escalate)\s+(me\s+)?(admin|root|sudo|superuser|administrator)\s+(rights?|privileges?|access|permissions?)",
            r"(i\s+(am|have|need))\s+(now\s+)?(an?\s+)?(admin|root|superuser|sudo|administrator)",
            r"(act|behave|treat\s+me)\s+as\s+(an?\s+)?(admin|root|superuser|sudo|administrator)",
            # ── PT-BR ──
            r"(me\s+)?(d[êe]|conceda|elev[ae]|promova)\s+(privil[ée]gios?|permiss[õo]es?|acesso|direitos?)\s+(de\s+)?(admin|administrador|root|sudo|super\s*usu[áa]rio|administrativos?)",
            r"(me\s+)?(trate|considere|reconhe[çc]a)\s+como\s+(um\s+)?(admin|administrador|root|sudo|super\s*usu[áa]rio)",
            r"(eu|agora)\s+(sou|tenho)\s+(privil[ée]gios?|permiss[õo]es?|acesso)\s+(de\s+)?(admin|administrador|root|sudo)",
            r"escale\s+(meus?\s+)?(privil[ée]gios?|permiss[õo]es?)",
            r"(habilite|libere|ative)\s+(modo\s+)?(admin|administrador|root|sudo|super\s*usu[áa]rio|debug)",
        ],
        weight=0.83,
        description="Tentativa de escalada de privilégio via prompt",
        justification_pt=(
            "O usuário tenta induzir o modelo a tratá-lo como administrador, "
            "root ou superusuário. Isso é uma tentativa de manipulação de "
            "controle de acesso por engenharia de prompt."
        ),
        policy_hint="Escalada de Privilégio",
    ),
    AttackPattern(
        name="harmful_content_pt",
        owasp_category="LLM06:SensitiveInformationDisclosure",
        patterns=[
            # Conteúdo perigoso solicitado em PT-BR — fora do gatilho crítico mas
            # ainda relevante. Mantém peso médio para permitir auditoria.
            r"como\s+(fa[çc]o|posso)\s+(para\s+)?(invadir|hackear|atacar|burlar|quebrar|descriptografar)",
            r"como\s+(fa[çc]o|posso)\s+(para\s+)?(roubar|fraudar|clonar)\s+(cart[ãa]o|conta|identidade|dados)",
            r"como\s+(criar|fabricar|fazer|montar)\s+(uma\s+)?(arma|bomba|explosivo|drog[ao])",
            r"me\s+ensine\s+a\s+(invadir|hackear|fraudar|enganar|burlar)",
            r"(t[ée]cnicas|m[ée]todos)\s+(para\s+)?(phishing|engenharia\s+social|ransomware|fraude)",
        ],
        weight=0.78,
        description="Solicitação de conteúdo violento, ilícito ou de fraude",
        justification_pt=(
            "A solicitação pede instruções para conduta ilícita ou perigosa "
            "(invasão, fraude, fabricação de arma, engenharia social ofensiva). "
            "Categoria de uso inaceitável."
        ),
        policy_hint="Conteúdo Violento / Ilícito",
    ),
]

# Padrões de strings perigosas (alta severidade - bloqueio imediato)
CRITICAL_PATTERNS = [
    r"(how\s+to\s+)?(make|create|build|synthesize|produce)\s+(a\s+)?(bomb|explosive|weapon|malware|virus|ransomware)",
    r"(instructions?\s+(for|on|to)\s+)?(making|creating|building)\s+(drugs?|meth|cocaine|heroin)",
    r"(child|minors?|underage)\s+(sexual|nude|naked|explicit)",
    r"(hack|exploit|attack)\s+(this|the)\s+(website|server|system|network)",
    r"social\s+security\s+number[s]?\s*(of|for)\s+(all|every|the)\s+(user|customer|employee|person)",
]


class InputGuard:
    """
    Firewall semântico para análise de entrada
    Alinhado ao OWASP LLM Top-10
    """

    def __init__(self):
        self.compiled_patterns = self._compile_patterns()
        self.compiled_critical = [
            re.compile(p, re.IGNORECASE | re.DOTALL)
            for p in CRITICAL_PATTERNS
        ]

    def _compile_patterns(self) -> List[Tuple[AttackPattern, List[re.Pattern]]]:
        compiled = []
        for attack in ATTACK_PATTERNS:
            patterns = [
                re.compile(p, re.IGNORECASE | re.DOTALL)
                for p in attack.patterns
            ]
            compiled.append((attack, patterns))
        return compiled

    def evaluate(self, prompt: str) -> Dict:
        """
        Avalia um prompt contra todas as categorias e retorna estrutura
        rica: labels, score, hits de política, justificativas em PT-BR,
        categorias OWASP e prompt sanitizado.
        """
        detected_attacks: List[str] = []
        policy_hits: List[str] = []          # mensagens curtas (compat retro)
        justifications: List[str] = []       # explicações longas em PT-BR
        policy_hints: List[str] = []         # nomes de política sugerida
        owasp_categories: List[str] = []
        total_score = 0.0
        blocked = False

        # ─── 1. Padrões críticos: bloqueio imediato ─────────────────────
        for pattern in self.compiled_critical:
            if pattern.search(prompt):
                blocked = True
                detected_attacks.append("critical_content")
                policy_hits.append("CRÍTICO: conteúdo extremamente perigoso detectado")
                justifications.append(
                    "Foi detectada solicitação de conteúdo extremamente perigoso "
                    "(armamento, drogas, abuso de menores, exploração ofensiva). "
                    "Bloqueio imediato e auditoria obrigatória."
                )
                policy_hints.append("Conteúdo Crítico — Bloqueio Imediato")
                total_score = 100.0
                owasp_categories.append("LLM06:SensitiveInformationDisclosure")
                break

        # ─── 2. Padrões semânticos por categoria ────────────────────────
        if not blocked:
            for attack, patterns in self.compiled_patterns:
                for pattern in patterns:
                    if pattern.search(prompt):
                        if attack.name not in detected_attacks:
                            detected_attacks.append(attack.name)
                            policy_hits.append(
                                f"{attack.owasp_category}: {attack.description}")
                            if attack.justification_pt:
                                justifications.append(attack.justification_pt)
                            if attack.policy_hint:
                                policy_hints.append(attack.policy_hint)
                            if attack.owasp_category not in owasp_categories:
                                owasp_categories.append(attack.owasp_category)
                            total_score += attack.weight * 100
                        break

            # Normalização do score acumulado.
            if total_score > 0:
                total_score = min(
                    100.0,
                    total_score / max(1, len(detected_attacks))
                    * (1 + len(detected_attacks) * 0.30),
                )

            # Bloqueio: score alto OU múltiplos vetores de alto peso OU
            # qualquer detecção em categorias críticas (credencial, .env etc).
            categorias_bloqueio_direto = {
                "credential_request",
                "system_prompt_disclosure",
                "internal_data_request",
                "data_exfiltration",
                "privilege_escalation",
            }
            high_weight_attacks = [
                a for a in detected_attacks
                if any(atk.name == a and atk.weight >= 0.8 for atk in ATTACK_PATTERNS)
            ]
            blocked = (
                total_score >= 75.0
                or len(high_weight_attacks) >= 2
                or any(a in categorias_bloqueio_direto for a in detected_attacks)
            )

        # ─── 3. Composição da justificativa textual final ───────────────
        if not detected_attacks:
            justification_text = (
                "Nenhum padrão de ataque conhecido foi acionado. O prompt foi "
                "considerado benigno pelo InputGuard nesta avaliação."
            )
        else:
            cabecalho = (
                "Bloqueado pelo firewall semântico." if blocked
                else "Sinalizado para auditoria — não bloqueado nesta camada."
            )
            justification_text = cabecalho + " " + " ".join(justifications)

        sanitized = self._sanitize(prompt, detected_attacks)

        return {
            "blocked": blocked,
            "labels": detected_attacks,
            "score": round(total_score, 2),
            "policy_hits": policy_hits,
            "policy_hints": policy_hints,
            "justification": justification_text,
            "sanitized_prompt": sanitized,
            "owasp_categories": owasp_categories,
        }

    def _sanitize(self, prompt: str, detected_attacks: List[str]) -> str:
        """Remove ou neutraliza partes maliciosas do prompt"""
        sanitized = prompt
        if detected_attacks:
            # Remover padrões de injeção mais comuns
            for attack, patterns in self.compiled_patterns:
                if attack.name in detected_attacks:
                    for pattern in patterns:
                        sanitized = pattern.sub("[REDACTED]", sanitized)
        return sanitized


# Singleton
input_guard = InputGuard()
