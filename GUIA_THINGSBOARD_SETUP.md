# 📊 Guia: Configuração do ThingsBoard

## ✅ Status Atual

- ✅ **Código implementado** - Cliente ThingsBoard criado
- ✅ **Integração no endpoint** - Dados são enviados automaticamente ao fazer predições
- ✅ **Docker Compose atualizado** - ThingsBoard habilitado
- ⏳ **Aguardando inicialização** - ThingsBoard leva alguns minutos para iniciar

---

## 🚀 Como Habilitar o ThingsBoard

### **Passo 1: Criar Banco de Dados**

O ThingsBoard precisa de um banco de dados separado. Já foi adicionado no `init.sql`, mas se o banco já existia, você precisa criar manualmente:

```bash
# Acessar PostgreSQL
docker exec -it hubfolio_postgres psql -U hubfolio_user -d hubfolio

# Criar banco para ThingsBoard
CREATE DATABASE thingsboard;
\q
```

### **Passo 2: Subir o ThingsBoard**

```bash
docker-compose up -d thingsboard
```

**Atenção:** O ThingsBoard pode levar **3-5 minutos** para inicializar completamente!

### **Passo 3: Verificar Status**

```bash
# Ver logs (aguarde até ver "Started ThingsBoard")
docker-compose logs -f thingsboard

# Verificar se está rodando
docker-compose ps thingsboard
```

### **Passo 4: Acessar ThingsBoard**

1. **Aguarde 3-5 minutos** após subir o container
2. Acesse: **http://localhost:8080**
3. **Credenciais padrão:**
   - Username: `tenant@thingsboard.org`
   - Password: `tenant`

---

## 📱 Configuração no ThingsBoard

### **Passo 1: Criar Dispositivo**

1. Faça login no ThingsBoard
2. Vá em **"Devices"** → **"Add device"**
3. Nome: **"HubFólio Predictions"**
4. Tipo: **"Default"**
5. Clique em **"Add"**

### **Passo 2: Obter Device Token**

1. Clique no dispositivo criado
2. Vá na aba **"Credentials"**
3. Copie o **"Access token"** (ex: `hubfolio-device-token-123`)

### **Passo 3: Configurar Token no Docker**

Edite o `docker-compose.yml` e atualize:

```yaml
environment:
  THINGSBOARD_DEVICE_TOKEN: seu-token-aqui
```

Ou configure via variável de ambiente:

```bash
export THINGSBOARD_DEVICE_TOKEN=seu-token-aqui
docker-compose restart fastapi
```

---

## 🧪 Testar Envio de Dados

### **Fazer uma Predição**

```bash
curl -X POST "http://localhost:8001/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "projetos_min": 3,
    "habilidades_min": 10,
    "kw_contexto": 4,
    "kw_processo": 3,
    "kw_resultado": 4,
    "consistencia_visual_score": 80,
    "bio": true,
    "contatos": true
  }'
```

### **Verificar Logs**

```bash
docker-compose logs fastapi | grep ThingsBoard
```

Você deve ver:
```
✅ Telemetria enviada para ThingsBoard: X campos
```

### **Ver no ThingsBoard**

1. Acesse: http://localhost:8080
2. Vá em **"Devices"** → **"HubFólio Predictions"**
3. Clique em **"Latest telemetry"**
4. Você verá os dados:
   - `predicted_iq`
   - `portfolio_id`
   - `model_name`
   - `classification`
   - `user_id`
   - `prediction_id`

---

## 📊 Criar Dashboard

### **Passo 1: Criar Dashboard**

1. Vá em **"Dashboards"** → **"Add dashboard"**
2. Nome: **"HubFólio Analytics"**
3. Clique em **"Add"**

### **Passo 2: Adicionar Widgets**

1. Clique no dashboard criado
2. Clique em **"Edit"** (lápis)
3. Clique em **"Add widget"**

#### **Widget 1: Time Series Chart (IQ ao longo do tempo)**

1. Tipo: **"Time series"**
2. Data source: **"HubFólio Predictions"**
3. Telemetry: **"predicted_iq"**
4. Time range: **"Last 24 hours"**
5. Salve

#### **Widget 2: Gauge (IQ Médio)**

1. Tipo: **"Gauge"**
2. Data source: **"HubFólio Predictions"**
3. Telemetry: **"predicted_iq"**
4. Function: **"Average"**
5. Range: **0-100**
6. Salve

#### **Widget 3: Table (Predições Recentes)**

1. Tipo: **"Table"**
2. Data source: **"HubFólio Predictions"**
3. Colunas:
   - `predicted_iq`
   - `classification`
   - `portfolio_id`
   - `user_id`
4. Salve

#### **Widget 4: Pie Chart (Distribuição de Classificações)**

1. Tipo: **"Pie chart"**
2. Data source: **"HubFólio Predictions"**
3. Telemetry: **"classification"**
4. Function: **"Count"**
5. Salve

---

## 🔍 Verificar se Está Funcionando

### **1. Verificar Container**

```bash
docker-compose ps thingsboard
```

**Status esperado:** `Up (healthy)` ou `Up` (pode levar alguns minutos)

### **2. Verificar Logs**

```bash
docker-compose logs thingsboard --tail 50
```

**Procure por:**
- `Started ThingsBoard`
- `Application started`
- Sem erros de conexão com banco

### **3. Verificar API**

```bash
curl http://localhost:8080/api/health
```

**Resposta esperada:** Status 200

### **4. Verificar Envio de Dados**

```bash
# Fazer uma predição
curl -X POST "http://localhost:8001/predict" ...

# Ver logs
docker-compose logs fastapi | grep -i thingsboard
```

---

## ⚠️ Problemas Comuns

### **ThingsBoard não inicia**

**Solução:**
1. Verifique se o banco `thingsboard` foi criado
2. Aguarde mais tempo (pode levar 5+ minutos)
3. Verifique os logs: `docker-compose logs thingsboard`

### **Erro de conexão com banco**

**Solução:**
```bash
# Criar banco manualmente
docker exec -it hubfolio_postgres psql -U hubfolio_user -d hubfolio -c "CREATE DATABASE thingsboard;"
```

### **Dados não aparecem**

**Solução:**
1. Verifique se o Device Token está correto
2. Verifique se o dispositivo foi criado no ThingsBoard
3. Verifique os logs: `docker-compose logs fastapi | grep ThingsBoard`

### **ThingsBoard muito lento**

**Normal!** O ThingsBoard é pesado e pode levar vários minutos para inicializar completamente.

---

## 📝 Resumo

### **O que foi implementado:**

1. ✅ **Cliente ThingsBoard** (`thingsboard_client.py`)
2. ✅ **Integração no endpoint** `/predict`
3. ✅ **Docker Compose** configurado
4. ✅ **Banco de dados** criado automaticamente

### **O que você precisa fazer:**

1. ⏳ **Aguardar inicialização** (3-5 minutos)
2. 🔑 **Criar dispositivo** no ThingsBoard
3. 🔑 **Copiar Device Token**
4. ⚙️ **Configurar token** no docker-compose.yml
5. 📊 **Criar dashboard** (opcional)

---

## 🎯 Próximos Passos

1. **Subir ThingsBoard:**
   ```bash
   docker-compose up -d thingsboard
   ```

2. **Aguardar inicialização** (3-5 minutos)

3. **Acessar:** http://localhost:8080

4. **Criar dispositivo** e copiar token

5. **Configurar token** no docker-compose.yml

6. **Fazer predições** e ver dados aparecerem!

**Tudo pronto para usar!** 🚀

