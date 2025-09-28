# Ejemplos de Integración - Intelligent Agent API

Este documento contiene ejemplos prácticos de cómo integrar sistemas externos con el Intelligent Agent API.

## 🚀 Inicio Rápido

### Verificar que el Servicio Esté Ejecutándose

```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "service": "intelligent_agent",
  "statistics": {
    "available_tables": 28,
    "service_status": "operational"
  }
}
```

---

## 🌐 Ejemplos por Tecnología

### 📱 Frontend Web (Vanilla JavaScript)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Intelligent Agent Client</title>
</head>
<body>
    <div>
        <input type="text" id="queryInput" placeholder="Escribe tu consulta aquí...">
        <button onclick="consultarAgente()">Consultar</button>
    </div>
    <div id="resultado"></div>

    <script>
        async function consultarAgente() {
            const query = document.getElementById('queryInput').value;
            const resultDiv = document.getElementById('resultado');

            try {
                resultDiv.innerHTML = 'Procesando...';

                const response = await fetch('http://localhost:8000/api/v1/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        human_query: query,
                        limit_results: 20
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    resultDiv.innerHTML = `
                        <h3>Respuesta:</h3>
                        <p>${data.answer}</p>
                        <h4>SQL Generado:</h4>
                        <code>${data.sql_query}</code>
                        <h4>Tiempo:</h4>
                        <p>${data.execution_time.toFixed(3)}s</p>
                    `;
                } else {
                    resultDiv.innerHTML = `<p style="color: red;">Error: ${data.error}</p>`;
                }
            } catch (error) {
                resultDiv.innerHTML = `<p style="color: red;">Error de conexión: ${error.message}</p>`;
            }
        }
    </script>
</body>
</html>
```

### ⚛️ React Component

```jsx
import React, { useState } from 'react';

const IntelligentAgentClient = () => {
    const [query, setQuery] = useState('');
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const API_BASE = 'http://localhost:8000/api/v1';

    const consultarAgente = async () => {
        if (!query.trim()) return;

        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const response = await fetch(`${API_BASE}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    human_query: query,
                    include_table_info: false,
                    limit_results: 50
                })
            });

            const data = await response.json();

            if (response.ok) {
                setResult(data);
            } else {
                setError(data.error || 'Error desconocido');
            }
        } catch (err) {
            setError(`Error de conexión: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="intelligent-agent-client">
            <div className="input-section">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Escribe tu consulta en español..."
                    onKeyPress={(e) => e.key === 'Enter' && consultarAgente()}
                />
                <button onClick={consultarAgente} disabled={loading}>
                    {loading ? 'Consultando...' : 'Consultar'}
                </button>
            </div>

            {error && (
                <div className="error">
                    <h3>Error:</h3>
                    <p>{error}</p>
                </div>
            )}

            {result && (
                <div className="result">
                    <h3>Respuesta:</h3>
                    <p>{result.answer}</p>

                    <h4>SQL Generado:</h4>
                    <pre><code>{result.sql_query}</code></pre>

                    <h4>Datos Crudos:</h4>
                    <pre><code>{JSON.stringify(result.raw_data, null, 2)}</code></pre>

                    <p><small>Tiempo de ejecución: {result.execution_time.toFixed(3)}s</small></p>
                </div>
            )}
        </div>
    );
};

export default IntelligentAgentClient;
```

### 🐍 Python - Clase Completa de Cliente

```python
import requests
import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class QueryResult:
    answer: str
    sql_query: str
    raw_data: List[Dict[str, Any]]
    execution_time: float
    timestamp: str
    table_info: Optional[str] = None

class IntelligentAgentClient:
    """Cliente Python para el Intelligent Agent API."""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)

    def health_check(self) -> Dict[str, Any]:
        """Verificar el estado del servicio."""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/health", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error en health check: {e}")
            raise

    def get_tables(self) -> List[str]:
        """Obtener lista de tablas disponibles."""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/tables", timeout=self.timeout)
            response.raise_for_status()
            return response.json()["tables"]
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error obteniendo tablas: {e}")
            raise

    def query(self,
             human_query: str,
             include_table_info: bool = False,
             limit_results: Optional[int] = None) -> QueryResult:
        """Realizar consulta en lenguaje natural."""

        payload = {
            "human_query": human_query,
            "include_table_info": include_table_info,
            "limit_results": limit_results
        }

        try:
            self.logger.info(f"Enviando consulta: {human_query[:50]}...")

            response = self.session.post(
                f"{self.base_url}/api/v1/query",
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                return QueryResult(**data)
            else:
                error_data = response.json()
                error_msg = error_data.get('error', 'Error desconocido')
                raise Exception(f"Error del servidor ({response.status_code}): {error_msg}")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error en consulta: {e}")
            raise

    def validate_sql(self, sql_query: str) -> Dict[str, Any]:
        """Validar una consulta SQL."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/validate-sql",
                data={"sql_query": sql_query},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error validando SQL: {e}")
            raise

# Ejemplo de uso
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)

    # Crear cliente
    client = IntelligentAgentClient()

    try:
        # Verificar estado
        health = client.health_check()
        print(f"Estado del servicio: {health['status']}")

        # Obtener tablas
        tables = client.get_tables()
        print(f"Tablas disponibles: {len(tables)}")

        # Realizar consultas
        consultas = [
            "¿Cuántos productos hay en total?",
            "¿Qué productos tienen stock bajo?",
            "Muéstrame las últimas transferencias"
        ]

        for consulta in consultas:
            print(f"\n--- Consulta: {consulta} ---")
            result = client.query(consulta, limit_results=5)
            print(f"Respuesta: {result.answer}")
            print(f"SQL: {result.sql_query}")
            print(f"Resultados: {len(result.raw_data)} filas")
            print(f"Tiempo: {result.execution_time:.3f}s")

    except Exception as e:
        print(f"Error: {e}")
```

### ☕ Java - Cliente REST

```java
import java.io.IOException;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import java.time.Duration;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.annotation.JsonProperty;

public class IntelligentAgentClient {

    private final HttpClient httpClient;
    private final String baseUrl;
    private final ObjectMapper objectMapper;

    public IntelligentAgentClient(String baseUrl) {
        this.baseUrl = baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
        this.httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();
        this.objectMapper = new ObjectMapper();
    }

    public QueryResponse query(String humanQuery, Boolean includeTableInfo, Integer limitResults)
            throws IOException, InterruptedException {

        QueryRequest request = new QueryRequest(humanQuery, includeTableInfo, limitResults);
        String requestBody = objectMapper.writeValueAsString(request);

        HttpRequest httpRequest = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/api/v1/query"))
            .header("Content-Type", "application/json")
            .timeout(Duration.ofSeconds(30))
            .POST(HttpRequest.BodyPublishers.ofString(requestBody))
            .build();

        HttpResponse<String> response = httpClient.send(httpRequest,
            HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() == 200) {
            return objectMapper.readValue(response.body(), QueryResponse.class);
        } else {
            throw new RuntimeException("Error: " + response.statusCode() + " - " + response.body());
        }
    }

    public HealthResponse healthCheck() throws IOException, InterruptedException {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/api/v1/health"))
            .timeout(Duration.ofSeconds(10))
            .GET()
            .build();

        HttpResponse<String> response = httpClient.send(request,
            HttpResponse.BodyHandlers.ofString());

        return objectMapper.readValue(response.body(), HealthResponse.class);
    }

    // Clases de datos
    public static class QueryRequest {
        @JsonProperty("human_query")
        public String humanQuery;

        @JsonProperty("include_table_info")
        public Boolean includeTableInfo;

        @JsonProperty("limit_results")
        public Integer limitResults;

        public QueryRequest(String humanQuery, Boolean includeTableInfo, Integer limitResults) {
            this.humanQuery = humanQuery;
            this.includeTableInfo = includeTableInfo;
            this.limitResults = limitResults;
        }
    }

    public static class QueryResponse {
        public String answer;

        @JsonProperty("sql_query")
        public String sqlQuery;

        @JsonProperty("raw_data")
        public Object[] rawData;

        @JsonProperty("execution_time")
        public Double executionTime;

        public String timestamp;

        @JsonProperty("table_info")
        public String tableInfo;
    }

    public static class HealthResponse {
        public String status;
        public String service;
        public Object statistics;
    }

    // Ejemplo de uso
    public static void main(String[] args) {
        IntelligentAgentClient client = new IntelligentAgentClient("http://localhost:8000");

        try {
            // Verificar estado
            HealthResponse health = client.healthCheck();
            System.out.println("Estado: " + health.status);

            // Realizar consulta
            QueryResponse result = client.query("¿Cuántos productos hay en total?", false, 10);
            System.out.println("Respuesta: " + result.answer);
            System.out.println("SQL: " + result.sqlQuery);
            System.out.println("Tiempo: " + result.executionTime + "s");

        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
        }
    }
}
```

### 🚀 Go - Cliente HTTP

```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "time"
)

type IntelligentAgentClient struct {
    BaseURL    string
    HTTPClient *http.Client
}

type QueryRequest struct {
    HumanQuery      string `json:"human_query"`
    IncludeTableInfo bool  `json:"include_table_info"`
    LimitResults    *int   `json:"limit_results,omitempty"`
}

type QueryResponse struct {
    Answer        string        `json:"answer"`
    SQLQuery      string        `json:"sql_query"`
    RawData       []interface{} `json:"raw_data"`
    ExecutionTime float64       `json:"execution_time"`
    Timestamp     string        `json:"timestamp"`
    TableInfo     *string       `json:"table_info,omitempty"`
}

type HealthResponse struct {
    Status     string      `json:"status"`
    Service    string      `json:"service"`
    Statistics interface{} `json:"statistics"`
}

func NewIntelligentAgentClient(baseURL string) *IntelligentAgentClient {
    return &IntelligentAgentClient{
        BaseURL: baseURL,
        HTTPClient: &http.Client{
            Timeout: 30 * time.Second,
        },
    }
}

func (c *IntelligentAgentClient) Query(humanQuery string, includeTableInfo bool, limitResults *int) (*QueryResponse, error) {
    reqBody := QueryRequest{
        HumanQuery:       humanQuery,
        IncludeTableInfo: includeTableInfo,
        LimitResults:     limitResults,
    }

    jsonData, err := json.Marshal(reqBody)
    if err != nil {
        return nil, fmt.Errorf("error marshaling request: %w", err)
    }

    resp, err := c.HTTPClient.Post(
        c.BaseURL+"/api/v1/query",
        "application/json",
        bytes.NewBuffer(jsonData),
    )
    if err != nil {
        return nil, fmt.Errorf("error making request: %w", err)
    }
    defer resp.Body.Close()

    body, err := io.ReadAll(resp.Body)
    if err != nil {
        return nil, fmt.Errorf("error reading response: %w", err)
    }

    if resp.StatusCode != http.StatusOK {
        return nil, fmt.Errorf("server error %d: %s", resp.StatusCode, string(body))
    }

    var result QueryResponse
    if err := json.Unmarshal(body, &result); err != nil {
        return nil, fmt.Errorf("error unmarshaling response: %w", err)
    }

    return &result, nil
}

func (c *IntelligentAgentClient) HealthCheck() (*HealthResponse, error) {
    resp, err := c.HTTPClient.Get(c.BaseURL + "/api/v1/health")
    if err != nil {
        return nil, fmt.Errorf("error making request: %w", err)
    }
    defer resp.Body.Close()

    var health HealthResponse
    if err := json.NewDecoder(resp.Body).Decode(&health); err != nil {
        return nil, fmt.Errorf("error decoding response: %w", err)
    }

    return &health, nil
}

func main() {
    client := NewIntelligentAgentClient("http://localhost:8000")

    // Verificar estado
    health, err := client.HealthCheck()
    if err != nil {
        fmt.Printf("Error en health check: %v\n", err)
        return
    }
    fmt.Printf("Estado del servicio: %s\n", health.Status)

    // Realizar consulta
    limit := 10
    result, err := client.Query("¿Cuántos productos hay en total?", false, &limit)
    if err != nil {
        fmt.Printf("Error en consulta: %v\n", err)
        return
    }

    fmt.Printf("Respuesta: %s\n", result.Answer)
    fmt.Printf("SQL: %s\n", result.SQLQuery)
    fmt.Printf("Tiempo: %.3fs\n", result.ExecutionTime)
}
```

---

## 🔧 Herramientas de Testing

### Postman Collection

```json
{
    "info": {
        "name": "Intelligent Agent API",
        "description": "Colección para probar el Intelligent Agent API"
    },
    "item": [
        {
            "name": "Health Check",
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{base_url}}/api/v1/health",
                    "host": ["{{base_url}}"],
                    "path": ["api", "v1", "health"]
                }
            }
        },
        {
            "name": "Query - Productos Total",
            "request": {
                "method": "POST",
                "header": [
                    {
                        "key": "Content-Type",
                        "value": "application/json"
                    }
                ],
                "body": {
                    "mode": "raw",
                    "raw": "{\n  \"human_query\": \"¿Cuántos productos hay en total?\",\n  \"limit_results\": 100\n}"
                },
                "url": {
                    "raw": "{{base_url}}/api/v1/query",
                    "host": ["{{base_url}}"],
                    "path": ["api", "v1", "query"]
                }
            }
        },
        {
            "name": "Get Tables",
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{base_url}}/api/v1/tables",
                    "host": ["{{base_url}}"],
                    "path": ["api", "v1", "tables"]
                }
            }
        }
    ],
    "variable": [
        {
            "key": "base_url",
            "value": "http://localhost:8000"
        }
    ]
}
```

### Script de Performance Testing

```bash
#!/bin/bash

# performance_test.sh
# Script para probar performance del API

BASE_URL="http://localhost:8000"
CONCURRENT_REQUESTS=10
TOTAL_REQUESTS=100

echo "Testing Intelligent Agent API Performance"
echo "=========================================="

# Test Health Endpoint
echo "Testing /health endpoint..."
curl -w "@curl-format.txt" -s -o /dev/null "$BASE_URL/api/v1/health"

# Test Query Endpoint
echo -e "\nTesting /query endpoint..."

# Crear archivo de formato para curl
cat > curl-format.txt << 'EOF'
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
EOF

# Test with apache bench (si está disponible)
if command -v ab &> /dev/null; then
    echo -e "\nRunning load test with Apache Bench..."
    ab -n $TOTAL_REQUESTS -c $CONCURRENT_REQUESTS -p query_payload.json -T application/json "$BASE_URL/api/v1/query"
fi

# Crear payload para testing
cat > query_payload.json << 'EOF'
{
  "human_query": "¿Cuántos productos hay en total?",
  "limit_results": 10
}
EOF

echo "Performance test completed!"
```

---

## 💡 Mejores Prácticas

### 1. Manejo de Errores

```python
def safe_query(client, query, max_retries=3):
    """Realizar consulta con reintentos automáticos."""
    for attempt in range(max_retries):
        try:
            return client.query(query)
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            raise
```

### 2. Cache de Resultados

```python
import hashlib
import pickle
from typing import Dict, Any

class CachedAgentClient:
    def __init__(self, client, cache_ttl=300):  # 5 minutos
        self.client = client
        self.cache = {}
        self.cache_ttl = cache_ttl

    def query(self, human_query, **kwargs):
        # Crear clave de cache
        cache_key = hashlib.md5(
            f"{human_query}{kwargs}".encode()
        ).hexdigest()

        # Verificar cache
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_result

        # Realizar consulta
        result = self.client.query(human_query, **kwargs)

        # Guardar en cache
        self.cache[cache_key] = (result, time.time())

        return result
```

### 3. Pool de Conexiones

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retries():
    session = requests.Session()

    # Configurar reintentos
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )

    adapter = HTTPAdapter(
        pool_connections=10,
        pool_maxsize=20,
        max_retries=retry_strategy
    )

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session
```

---

## 🔍 Debugging y Troubleshooting

### Logs de Debug

```python
import logging

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Habilitar logs de requests
import http.client as http_client
http_client.HTTPConnection.debuglevel = 1

requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True
```

### Test de Conectividad

```bash
#!/bin/bash
# connectivity_test.sh

BASE_URL="http://localhost:8000"

echo "Testing connectivity to Intelligent Agent API..."

# Test 1: Basic connectivity
echo -n "Basic connectivity: "
if curl -s --max-time 5 "$BASE_URL" > /dev/null; then
    echo "OK"
else
    echo "FAIL"
    exit 1
fi

# Test 2: Health endpoint
echo -n "Health endpoint: "
HEALTH_STATUS=$(curl -s --max-time 10 "$BASE_URL/api/v1/health" | jq -r '.status' 2>/dev/null)
if [ "$HEALTH_STATUS" = "healthy" ]; then
    echo "OK"
else
    echo "FAIL (Status: $HEALTH_STATUS)"
fi

# Test 3: Query endpoint
echo -n "Query endpoint: "
QUERY_RESPONSE=$(curl -s --max-time 30 -X POST "$BASE_URL/api/v1/query" \
    -H "Content-Type: application/json" \
    -d '{"human_query": "test", "limit_results": 1}')

if echo "$QUERY_RESPONSE" | jq -e '.answer' > /dev/null 2>&1; then
    echo "OK"
else
    echo "FAIL"
    echo "Response: $QUERY_RESPONSE"
fi

echo "Connectivity test completed!"
```

Este conjunto de ejemplos proporciona una base sólida para integrar cualquier sistema externo con tu Intelligent Agent API. Los desarrolladores pueden adaptar estos ejemplos según sus necesidades específicas y tecnologías preferidas.