# Variables de Entorno para Railway

Configura estas variables de entorno en tu proyecto de Railway:

## 🔑 Variables Requeridas

### Claude API Configuration
```
CLAUDE_API_KEY=tu_api_key_de_claude_aqui
CLAUDE_MODEL=claude-3-5-haiku-20241022
CLAUDE_DEMO_MODE=false
CLAUDE_FALLBACK_ENABLED=true
```

### Application Configuration
```
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8080
SECRET_KEY=tu-clave-secreta-super-segura-para-produccion-cambiar-esto
LOG_LEVEL=INFO
```

### Database Configuration (PostgreSQL Plugin)
```
# Estas variables se configuran automáticamente con el plugin PostgreSQL de Railway
# Solo asegúrate de tener conectado el plugin PostgreSQL
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
```

## 🚀 Instrucciones de Configuración en Railway

### 1. Crear Proyecto en Railway
```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login a Railway
railway login

# Crear nuevo proyecto
railway new
```

### 2. Configurar Base de Datos
1. Ve a tu proyecto en Railway dashboard
2. Agrega el plugin "PostgreSQL"
3. Las variables de conexión se configurarán automáticamente

### 3. Configurar Variables de Entorno
En el dashboard de Railway, ve a "Variables" y agrega:

```
CLAUDE_API_KEY=tu_api_key_de_claude
CLAUDE_MODEL=claude-3-5-haiku-20241022
CLAUDE_DEMO_MODE=false
CLAUDE_FALLBACK_ENABLED=true
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8080
SECRET_KEY=genera-una-clave-secreta-segura
LOG_LEVEL=INFO
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
```

### 4. Conectar Repositorio
1. Conecta tu repositorio GitHub
2. Railway detectará automáticamente el Dockerfile
3. El despliegue se iniciará automáticamente

### 5. Configurar Dominio (Opcional)
1. Ve a "Settings" > "Domains"
2. Agrega un dominio personalizado o usa el dominio de Railway

## 🔧 Variables Automáticas de Railway

Railway configura automáticamente estas variables:
- `RAILWAY_ENVIRONMENT_NAME` - Nombre del entorno
- `RAILWAY_PUBLIC_DOMAIN` - Dominio público del servicio
- `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` - Conexión PostgreSQL

## 🛠️ Comandos Útiles

### Desplegar desde CLI
```bash
# Desplegar proyecto actual
railway up

# Ver logs en tiempo real
railway logs

# Abrir dashboard
railway open
```

### Verificar Variables
```bash
# Ver todas las variables configuradas
railway variables

# Agregar variable
railway variables set CLAUDE_API_KEY=tu_api_key
```

## 🔒 Seguridad

- ✅ Nunca commitear archivos `.env` con datos reales
- ✅ Usar claves secretas fuertes y únicas
- ✅ Rotar las API keys regularmente
- ✅ Configurar CORS apropiadamente
- ✅ Deshabilitar documentación en producción