#!/bin/bash
# LLM Trust & Safety Framework - Script de Inicialização

echo "🚀 Iniciando LLM Trust & Safety Framework..."

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado. Instale Python 3.11+"
    exit 1
fi

# Instalar dependências do backend
echo "📦 Instalando dependências do backend..."
cd backend
pip install -q -r requirements.txt

# Iniciar backend
echo "🔧 Iniciando Backend (FastAPI)..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

sleep 3
echo "✅ Backend rodando em http://localhost:8000"
echo "📖 Documentação API: http://localhost:8000/docs"
echo ""
echo "🔐 Credenciais padrão:"
echo "   admin / admin123"
echo "   analyst / analyst123"
echo "   viewer / viewer123"
echo ""
echo "Para parar: kill $BACKEND_PID"

wait $BACKEND_PID
