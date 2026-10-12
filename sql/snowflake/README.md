# Mapeamento e Carga Snowflake — Camada Curated ANAC (WS1)

Este diretório contém os scripts SQL para provisionamento e ingestão dos agregados curados da ANAC no **Snowflake**, assegurando paridade contratual estrita entre o ambiente de processamento local (DuckDB + Parquet) e o Data Cloud corporativo.

---

## 1. Princípio da Paridade Contratual

Conforme o Plano Mestre do Projeto Aura 2.0 (seção 1 e §WS1):
> **"Contrato de dados idêntico ao esperado no Snowflake: trocar sintético por dado real é troca de fonte, não reescrita."**

Cada tabela Snowflake criada em `ddl.sql` mapeia de forma exata as colunas, tipos de dados, nulabilidade e chaves primárias definidos nos schemas de governança em `schemas/`:

| Tabela Snowflake | Contrato YAML | Arquivo Parquet Curado | Granularidade |
|---|---|---|---|
| `AURA_CURATED.ANAC_ROUTES_MONTHLY` | `schemas/anac_routes_monthly.yaml` | `data/curated/anac/anac_routes_monthly.parquet` | Rota (origem-destino) × Mês |
| `AURA_CURATED.ANAC_AIRPORTS` | `schemas/anac_airports.yaml` | `data/curated/anac/anac_airports.parquet` | Aeródromo (código OACI) |
| `AURA_CURATED.ANAC_DELAYS_MONTHLY` | `schemas/anac_delays_monthly.yaml` | `data/curated/anac/anac_delays_monthly.parquet` | Mês do calendário |

---

## 2. Estrutura dos Arquivos

1. **`ddl.sql`**:
   - Criação da infraestrutura lógica: Warehouse (`AURA_WH`), Database (`AURA_DB`), Schemas (`AURA_RAW`, `AURA_CURATED`, `AURA_ANALYTICS`).
   - Definição do formato de arquivo `AURA_PARQUET_FORMAT` (`TYPE = PARQUET`).
   - Criação do Named Stage `AURA_STAGE_CURATED_ANAC`.
   - DDL das três tabelas da camada curada com constraints de chave primária e comentários auditáveis.

2. **`carga.sql`**:
   - Instruções de upload via SnowSQL (`PUT`).
   - Comandos `COPY INTO` utilizando `MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE` para ingestão resiliente.
   - Alternativa documentada para **External Tables** sobre data lake (AWS S3 / Azure Blob / GCP).
   - Queries de validação e controle de qualidade para validação imediata da carga.

---

## 3. Guia de Execução no Snowflake

### Passo 1: Executar o DDL
Execute o script `ddl.sql` em uma sessão autenticada com perfil `SYSADMIN` ou permissões equivalentes de criação de banco e warehouse:
```bash
snowsql -f sql/snowflake/ddl.sql
```

### Passo 2: Upload dos Arquivos Parquet para o Stage
Utilize o utilitário oficial `snowsql` para enviar os parquets locais para o stage nomeado:
```bash
snowsql -q "PUT file://data/curated/anac/anac_routes_monthly.parquet @AURA_DB.AURA_CURATED.AURA_STAGE_CURATED_ANAC/routes/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;"
snowsql -q "PUT file://data/curated/anac/anac_airports.parquet @AURA_DB.AURA_CURATED.AURA_STAGE_CURATED_ANAC/airports/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;"
snowsql -q "PUT file://data/curated/anac/anac_delays_monthly.parquet @AURA_DB.AURA_CURATED.AURA_STAGE_CURATED_ANAC/delays/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;"
```

### Passo 3: Executar a Carga e Validação
Execute `carga.sql` para carregar as tabelas e rodar os testes de integridade:
```bash
snowsql -f sql/snowflake/carga.sql
```

---

## 4. Notas de Mapeamento de Tipos e Limitações

1. **Tipos de Dados:**
   - Colunas textuais (OACI, rotas, códigos) são mapeadas para `VARCHAR` com limites definidos.
   - Volumes e passageiros usam `FLOAT` ou `NUMBER` para suportar tanto os agregados locais quanto futuras cargas de eventos individuais sem truncamento.
   - Colunas temporais (`ano_mes`) usam formato ISO string `AAAA-MM` para compatibilidade cross-engine (DuckDB e Snowflake).

2. **Limitações Declaradas:**
   - A execução em ambiente real depende de conta ativa e credenciais Snowflake (fora do ambiente local de CI/testes).
   - Para ambientes em nuvem produtivos, recomenda-se configurar External Stage apontando para bucket S3 com IAM Role (`STORAGE INTEGRATION`), substituindo o stage interno.
