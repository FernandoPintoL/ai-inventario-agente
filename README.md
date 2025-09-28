# Intelligent Agent API

Un agente inteligente avanzado que convierte consultas en lenguaje natural a SQL utilizando **Claude (Anthropic)**, Langchain y PostgreSQL para gestión de inventarios.

## 🚀 Características

- **Conversión NL-to-SQL**: Convierte preguntas en español a consultas SQL automáticamente
- **Powered by Claude**: Utiliza Claude 3.5 Haiku para procesamiento de lenguaje natural
- **Arquitectura Modular**: Código bien estructurado y mantenible
- **Manejo de Errores Robusto**: Validaciones y manejo de excepciones completo
- **Pool de Conexiones**: Gestión eficiente de conexiones a la base de datos
- **API REST Completa**: Endpoints documentados con FastAPI
- **Logging Estructurado**: Sistema de logs detallado para monitoreo
- **Validaciones de Seguridad**: Prevención de consultas SQL peligrosas
- **Sistema de Fallback**: Funciona con IA simulada cuando Claude no está disponible

## 📋 Requisitos

- Python 3.8+
- PostgreSQL 12+
- Cuenta de Claude API (Anthropic)

## 🛠️ Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <repository-url>
   cd AgenteInteligente
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones
   ```

5. **Configurar base de datos**
   - Crear base de datos PostgreSQL
   - Ejecutar el script SQL proporcionado para crear las tablas

## ⚙️ Configuración

Edita el archivo `.env` con tus configuraciones:

```env
# Claude Configuration
CLAUDE_API_KEY=tu_claude_api_key_aqui
CLAUDE_MODEL=claude-3-5-haiku-20241022
CLAUDE_DEMO_MODE=false
CLAUDE_FALLBACK_ENABLED=true

# Base de Datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tu_base_de_datos
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña

# Servidor
SERVER_URL=http://localhost:8000
SECRET_KEY=tu-clave-secreta

# Opcional
LOG_LEVEL=INFO
DB_POOL_SIZE=5
```

## 🏃‍♂️ Ejecución

### Desarrollo
```bash
python scripts/run_dev.py
```

### Producción
```bash
python main.py
```

### Pruebas de Conexión
```bash
python scripts/test_connection.py
```

## 🌐 Integración Externa

### URL Base del Servicio

```
http://localhost:8000
```

Para producción, reemplaza `localhost:8000` con tu dominio y puerto correspondiente.

### Autenticación

El servicio actualmente no requiere autenticación, pero es recomendable implementarla para producción mediante:
- API Keys
- JWT Tokens
- OAuth 2.0

---

## 📖 Documentación de API

### 🔍 Endpoint Principal: Consulta Natural

**POST** `/api/v1/query`

Convierte una consulta en lenguaje natural a SQL, la ejecuta y retorna una respuesta procesada.

#### Parámetros de Entrada

```json
{
  "human_query": "string (obligatorio, 1-1000 caracteres)",
  "include_table_info": "boolean (opcional, default: false)",
  "limit_results": "integer (opcional, 1-1000, default: null)"
}
```

#### Respuesta Exitosa (200)

```json
{
  "answer": "string - Respuesta en lenguaje natural",
  "sql_query": "string - Consulta SQL generada",
  "raw_data": "array - Datos crudos de la base de datos",
  "execution_time": "float - Tiempo de ejecución en segundos",
  "timestamp": "string - Timestamp ISO 8601",
  "table_info": "string - Información del esquema (si se solicita)"
}
```

#### Respuestas de Error

**400 Bad Request** - Error de validación
```json
{
  "error": "Descripción del error de validación",
  "error_type": "ValidationException",
  "details": {}
}
```

**422 Unprocessable Entity** - Error en generación SQL
```json
{
  "error": "No se pudo generar una consulta SQL válida para tu pregunta.",
  "error_type": "SQLGenerationException",
  "details": {}
}
```

**503 Service Unavailable** - Error de base de datos
```json
{
  "error": "Error de conexión con la base de datos.",
  "error_type": "DatabaseException",
  "details": {}
}
```

---

### 📊 Endpoints Auxiliares

#### Estado del Servicio

**GET** `/api/v1/health`

```json
{
  "status": "healthy",
  "service": "intelligent_agent",
  "statistics": {
    "available_tables": 28,
    "service_status": "operational",
    "supported_operations": ["SELECT queries", "Natural language processing"]
  }
}
```

#### Lista de Tablas

**GET** `/api/v1/tables`

```json
{
  "tables": [
    "almacenes",
    "productos",
    "stock_productos",
    "movimientos_inventario",
    "transferencia_inventarios",
    "categorias",
    "marcas",
    "precios_producto"
  ]
}
```

#### Esquema de Base de Datos

**GET** `/api/v1/schema?tables=productos,almacenes`

```json
{
  "available_tables": ["productos", "almacenes", "..."],
  "schema_info": "CREATE TABLE productos (...)",
  "filtered_tables": ["productos", "almacenes"]
}
```

#### Validar SQL

**POST** `/api/v1/validate-sql`

Body: `sql_query=SELECT * FROM productos`

```json
{
  "is_safe": true,
  "error_message": null,
  "query": "SELECT * FROM productos"
}
```

---

## 🧪 Ejemplos de Integración

### JavaScript/Node.js

```javascript
const axios = require('axios');

const API_BASE = 'http://localhost:8000/api/v1';

async function consultarInventario(pregunta) {
  try {
    const response = await axios.post(`${API_BASE}/query`, {
      human_query: pregunta,
      include_table_info: false,
      limit_results: 50
    });

    console.log('Respuesta:', response.data.answer);
    console.log('SQL generado:', response.data.sql_query);

    return response.data;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
    throw error;
  }
}

// Uso
consultarInventario("¿Cuántos productos hay en total?");
```

### Python

```python
import requests
import json

API_BASE = 'http://localhost:8000/api/v1'

def consultar_inventario(pregunta, limite=None):
    url = f"{API_BASE}/query"
    payload = {
        "human_query": pregunta,
        "include_table_info": False,
        "limit_results": limite
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        print(f"Respuesta: {data['answer']}")
        print(f"SQL: {data['sql_query']}")

        return data

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Detalles: {e.response.text}")
        raise

# Uso
resultado = consultar_inventario("¿Qué productos tienen stock bajo?", limite=10)
```

### C# (.NET)

```csharp
using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;

public class IntelligentAgentClient
{
    private readonly HttpClient _httpClient;
    private readonly string _baseUrl;

    public IntelligentAgentClient(string baseUrl = "http://localhost:8000")
    {
        _httpClient = new HttpClient();
        _baseUrl = baseUrl;
    }

    public async Task<QueryResponse> ConsultarInventarioAsync(string pregunta, int? limite = null)
    {
        var request = new QueryRequest
        {
            HumanQuery = pregunta,
            IncludeTableInfo = false,
            LimitResults = limite
        };

        var json = JsonConvert.SerializeObject(request);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        try
        {
            var response = await _httpClient.PostAsync($"{_baseUrl}/api/v1/query", content);
            response.EnsureSuccessStatusCode();

            var responseJson = await response.Content.ReadAsStringAsync();
            return JsonConvert.DeserializeObject<QueryResponse>(responseJson);
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"Error: {ex.Message}");
            throw;
        }
    }
}

public class QueryRequest
{
    [JsonProperty("human_query")]
    public string HumanQuery { get; set; }

    [JsonProperty("include_table_info")]
    public bool IncludeTableInfo { get; set; }

    [JsonProperty("limit_results")]
    public int? LimitResults { get; set; }
}

public class QueryResponse
{
    [JsonProperty("answer")]
    public string Answer { get; set; }

    [JsonProperty("sql_query")]
    public string SqlQuery { get; set; }

    [JsonProperty("execution_time")]
    public double ExecutionTime { get; set; }
}
```

### cURL

```bash
# Consulta básica
curl -X POST "http://localhost:8000/api/v1/query" \
     -H "Content-Type: application/json" \
     -d '{
       "human_query": "¿Cuántos productos hay en total?",
       "limit_results": 100
     }'

# Consulta con información de esquema
curl -X POST "http://localhost:8000/api/v1/query" \
     -H "Content-Type: application/json" \
     -d '{
       "human_query": "Muéstrame los productos con stock bajo",
       "include_table_info": true,
       "limit_results": 10
     }'

# Estado del servicio
curl -X GET "http://localhost:8000/api/v1/health"

# Lista de tablas
curl -X GET "http://localhost:8000/api/v1/tables"
```

---

## 💡 Ejemplos de Consultas Prácticas

### Inventario y Stock

| Consulta en Español | Tipo de Respuesta |
|---------------------|-------------------|
| "¿Cuántos productos hay en total?" | Número total de productos |
| "¿Qué productos tienen stock bajo?" | Lista de productos con stock mínimo |
| "Muéstrame el inventario del almacén principal" | Stock por producto en almacén específico |
| "¿Cuáles son los productos más vendidos?" | Ranking de productos por movimientos |

### Movimientos y Transferencias

| Consulta en Español | Tipo de Respuesta |
|---------------------|-------------------|
| "¿Cuáles fueron los últimos movimientos?" | Historial reciente de movimientos |
| "¿Qué transferencias están pendientes?" | Estado de transferencias |
| "Muéstrame los movimientos de hoy" | Movimientos del día actual |

### Precios y Categorías

| Consulta en Español | Tipo de Respuesta |
|---------------------|-------------------|
| "¿Cuál es el precio promedio de los productos?" | Valor promedio calculado |
| "Muéstrame los productos más caros" | Lista ordenada por precio |
| "¿Qué categorías tenemos disponibles?" | Lista de categorías activas |

### Ejemplo de Respuesta Completa

**Consulta:** "¿Cuántos productos hay por categoría?"

**Respuesta:**
```json
{
  "answer": "Aquí tienes la distribución de productos por categoría:\n- Electrónicos: 45 productos\n- Ropa: 32 productos\n- Hogar: 28 productos\n- Deportes: 15 productos\n- Libros: 12 productos",
  "sql_query": "SELECT c.nombre as categoria, COUNT(p.id) as cantidad FROM categorias c LEFT JOIN productos p ON c.id = p.categoria_id WHERE c.activo = true GROUP BY c.id, c.nombre ORDER BY cantidad DESC",
  "raw_data": [
    {"categoria": "Electrónicos", "cantidad": 45},
    {"categoria": "Ropa", "cantidad": 32},
    {"categoria": "Hogar", "cantidad": 28},
    {"categoria": "Deportes", "cantidad": 15},
    {"categoria": "Libros", "cantidad": 12}
  ],
  "execution_time": 0.234,
  "timestamp": "2024-09-27T20:30:45.123Z",
  "table_info": null
}
```

---

## 🔒 Consideraciones de Seguridad

### Validaciones Implementadas

- ✅ **Solo SELECT**: El sistema rechaza cualquier consulta que no sea SELECT
- ✅ **Sanitización**: Limpieza automática de consultas peligrosas
- ✅ **Límites**: Restricciones en tamaño de respuesta y timeout
- ✅ **Validación de entrada**: Verificación de formato y longitud

### Recomendaciones para Producción

1. **Implementar autenticación** (API Keys, JWT)
2. **Rate limiting** para prevenir abuso
3. **HTTPS** obligatorio
4. **Firewall** para restringir acceso
5. **Monitoreo** de consultas y performance
6. **Backup** regular de logs y configuración

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Sistema        │    │  Intelligent    │    │   Base de       │
│  Externo        │───▶│   Agent API     │───▶│   Datos         │
│                 │    │                 │    │  PostgreSQL     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                               ▼
                       ┌─────────────────┐
                       │   Claude API    │
                       │  (Anthropic)    │
                       └─────────────────┘
```

### Flujo de Procesamiento

1. **Recepción**: Sistema externo envía consulta en lenguaje natural
2. **Validación**: Verificación de formato y seguridad
3. **Procesamiento IA**: Claude convierte la consulta a SQL
4. **Ejecución**: Se ejecuta la consulta SQL en PostgreSQL
5. **Respuesta IA**: Claude genera respuesta en lenguaje natural
6. **Retorno**: Se envía respuesta estructurada al sistema externo

---

## 📊 Monitoreo y Logs

### Endpoints de Monitoreo

- `/api/v1/health` - Estado general del servicio
- `/` - Información básica de la API

### Archivos de Log

- `logs/app.log` - Log principal de la aplicación
- Rotación automática por tamaño
- Niveles: INFO, WARNING, ERROR

### Métricas Importantes

- Tiempo de respuesta promedio
- Tasa de éxito/fallo de consultas
- Uso de recursos (CPU, memoria)
- Conexiones activas a base de datos

---

## 🐛 Códigos de Error y Troubleshooting

### Errores Comunes

| Código | Descripción | Solución |
|--------|-------------|----------|
| 400 | Consulta mal formateada | Verificar formato JSON y parámetros |
| 422 | No se pudo generar SQL | Reformular la pregunta más claramente |
| 503 | Error de base de datos | Verificar conexión a PostgreSQL |
| 502 | Error de Claude API | Verificar API key y conectividad |

### Diagnóstico

1. **Verificar estado**: `GET /api/v1/health`
2. **Revisar logs**: `tail -f logs/app.log`
3. **Probar conexiones**: `python scripts/test_connection.py`

---

## 📝 Documentación Interactiva

Una vez que el servidor esté ejecutándose:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 🤝 Soporte y Contribución

### Obtener Ayuda

1. Revisar esta documentación
2. Consultar logs en `logs/app.log`
3. Ejecutar diagnósticos con `python scripts/test_connection.py`
4. Abrir issue en el repositorio

### Contribuir

1. Fork del proyecto
2. Crear rama de feature
3. Implementar cambios con tests
4. Crear Pull Request

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo [LICENSE](LICENSE) para más detalles.