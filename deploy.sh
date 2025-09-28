#!/bin/bash

# Script de despliegue rápido para Railway
# Uso: ./deploy.sh

set -e

echo "🚀 Iniciando despliegue en Railway..."

# Verificar que estamos en el directorio correcto
if [ ! -f "Dockerfile" ] || [ ! -f "railway.json" ]; then
    echo "❌ Error: No se encontraron archivos de configuración (Dockerfile, railway.json)"
    echo "   Asegúrate de estar en el directorio raíz del proyecto"
    exit 1
fi

# Verificar que Railway CLI esté instalado
if ! command -v railway &> /dev/null; then
    echo "❌ Error: Railway CLI no está instalado"
    echo "   Instalar con: npm install -g @railway/cli"
    exit 1
fi

# Verificar login en Railway
if ! railway whoami &> /dev/null; then
    echo "🔐 Iniciando sesión en Railway..."
    railway login
fi

# Verificar que el proyecto está conectado
if ! railway status &> /dev/null; then
    echo "🔗 Conectando proyecto a Railway..."
    echo "   Elige 'Create new project' o 'Link existing project'"
    railway link
fi

# Verificar variables de entorno críticas
echo "🔍 Verificando configuración..."

REQUIRED_VARS=("CLAUDE_API_KEY" "SECRET_KEY" "ENVIRONMENT")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if ! railway variables get "$var" &> /dev/null; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo "⚠️  Variables faltantes detectadas:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "📝 Por favor configura las variables en Railway dashboard:"
    echo "   railway open"
    echo ""
    echo "   Variables requeridas:"
    echo "   - CLAUDE_API_KEY=tu_api_key_de_claude"
    echo "   - SECRET_KEY=una_clave_secreta_muy_segura"
    echo "   - ENVIRONMENT=production"
    echo "   - PORT=8080"
    echo ""
    read -p "¿Continuar con el despliegue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "🛑 Despliegue cancelado"
        exit 1
    fi
fi

# Verificar plugins de base de datos
echo "🗄️  Verificando base de datos..."
if ! railway plugins | grep -q "postgresql"; then
    echo "⚠️  Plugin PostgreSQL no detectado"
    echo "   Agrega el plugin PostgreSQL en Railway dashboard:"
    echo "   railway open"
    echo ""
    read -p "¿Continuar sin verificar BD? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "🛑 Despliegue cancelado"
        exit 1
    fi
fi

# Mostrar información del proyecto
echo ""
echo "📋 Información del proyecto:"
railway status

# Confirmar despliegue
echo ""
read -p "🚀 ¿Proceder con el despliegue? (Y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "🛑 Despliegue cancelado"
    exit 1
fi

# Realizar despliegue
echo "🚀 Desplegando en Railway..."
railway up

# Esperar un momento para que el servicio se inicie
echo "⏳ Esperando que el servicio se inicie..."
sleep 10

# Obtener URL del servicio
echo ""
echo "🌐 Obteniendo URL del servicio..."
URL=$(railway domain)

if [ -n "$URL" ]; then
    echo ""
    echo "✅ ¡Despliegue completado exitosamente!"
    echo ""
    echo "🌐 URLs de tu API:"
    echo "   Servicio principal: https://$URL"
    echo "   Health check:      https://$URL/api/v1/health"
    echo "   Endpoint consulta: https://$URL/api/v1/query"
    echo ""
    echo "🔍 Verificando servicio..."

    # Verificar health check
    if curl -s "https://$URL/api/v1/health" > /dev/null; then
        echo "✅ Servicio respondiendo correctamente"
    else
        echo "⚠️  Servicio no responde (puede estar iniciando)"
        echo "   Verifica logs con: railway logs"
    fi

    echo ""
    echo "📊 Comandos útiles:"
    echo "   Ver logs:        railway logs"
    echo "   Ver dashboard:   railway open"
    echo "   Ver variables:   railway variables"
    echo "   Ver métricas:    railway metrics"

else
    echo "⚠️  No se pudo obtener la URL del servicio"
    echo "   Verifica el estado con: railway status"
    echo "   Ver logs con: railway logs"
fi

echo ""
echo "🎉 ¡Proceso de despliegue finalizado!"