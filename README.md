# Amazonia Minada API

Esse repositório contém o código fonte da API REST do Amazônia Minada, projeto do Infoamazônia que monitora os requerimentos minerários em unidades de conservação integral e em terras indígenas na Amazônia Legal brasileira. Essa API contém métodos que calculam estatísticas a respeito dos requerimentos minerários coletados pelo [bot do Amazônia Minada](https://github.com/InfoAmazonia/amazonia-minada), a partir dos dados fornecidos pela Agência Nacional de Mineração (ANM), em termos da área declarada (área total dos requerimentos) e da incidência (quantidade de requerimentos).

**Como executar**
---
Para colocar o servidor em execução, inicialmente é necessário criar um arquivo .env com as configurações do banco de dados MongoDB do Amazônia Minada, do qual serão extraídos os dados.

    $ cp .env.example .env

Preencha as informações necessárias no arquivo .env. Em seguida, para rodar a aplicação em ambiente de produção utilizando o docker, execute:

    $ docker-compose up -d --build
    
Para executar em ambiente de desenvolvimento, execute o comando para instalar as dependências:

    $ yarn install
    
Em seguida, rode o container de desenvolvimento:

    $ docker-compose -f docker-compose-dev.yml up -d --build 

# Documentação da API

**Busca Geral**
----
Método que permite uma busca geral para Substância, Estado, Solicitante (Empresa), Terras Indígenas, Unidades de Conservação ou Etnias de Terras Indígenas, retornando as opções disponíveis no Banco de Dados que são iniciadas ou que possuem alguma palavra iniciada com a string fornecida.

* **URL:**
  
      /api/search/:searchTerm

* **Método:**

  `GET`

* **Parâmetros na URL:**

  **Obrigatórios:**
          
    - searchTerm:[string] - Palavra que será utilizada na busca

* **Parâmetros no Body:**

  Nenhum

* **Exemplo:**

      /api/search/amaz

* **Resposta:**

    * **Código:** <span style="color:green">**200**</span> <br/>
      **Conteúdo:**

      ```javascript
        [
          {
            "type": "state",
            "value": "Amazonas"
          },
          {
            "type": "company",
            "value": "AMAZON GLOBAL CONSULT LTDA"
          },
          {
            "type": "company",
            "value": "Amazonas Exploração e Mineração Ltda."
          },
          {
            "type": "company",
            "value": "AMAZON STONE S.A."
          },
          {
            "type": "company",
            "value": "Amazonas Comercio Atacadista de Joias e Participaçoes Ltda Epp"
          }
        ]
      ```
      **Descrição:** Retorna um array de objetos contendo o tipo de dado [substance (substância), company (solicitante), state (estado), reserve (terra indígena), unity (unidade de conservação) ou reserveEthnicity (etnia de terras indígenas)] e o valor (nome) das opções que são iniciadas pela string determinada.
      
    * **Código:** <span style="color:red">**500**</span> <br />
      **Conteúdo:**
      ```javascript
      {
        "message": "Internal Server Error"
      }
      ```
      **Descrição:** Erro interno do servidor.


**Listar Requerimentos**
----
Método que permite uma filtragem dos requerimentos minerários em Unidades de Conservação e em Terras Indígenas. 

* **URL:**
  
      /api/invasions

* **Método:**

  `POST`

* **Parâmetros na URL:**

  - page?:[number] - Número da página de registros a ser retornada, retorna a primeira página caso um número não seja informado.
  - pageSize?:[number] - Número de requerimentos por página, caso não seja informado são retornados 10 por página.
  - output?:[string] - Formato de saída (permitidos: csv).

* **Parâmetros no Body:**

  ```javascript
  {
    "filters": {
      "state": [], //Array de strings com o nome dos estados
      "company": [], //Array de strings com o nome das empresas
      "reserve": [], //Array de strings com o nome das Terras Indígenas
      "unity": [], //Array de strings com o nome das Unidades de Conservação
      "year": [], //Array de inteiros com os anos
      "substance": [], //Array de strings com o nome das substâncias
      "reservePhase": [], //Array de strings com as fases do processo de homologação das terras indígenas
      "reserveEthnicity": [], //Array de strings com o nome das etinias de terras indígenas
      "requirementPhase": [], //Array de strings com as fases dos requerimentos de mineração
      "use": [], //Array de strings com os usos declarados dos requerimentos de mineração
    },
    "enableUnity": true, //Boolean para ativar/desativar dados de ucs (default: true)
    "enableReserve": true, //Boolean para ativar/desativar dados de Terras Indígenas (default: true)
  }
  ```
  **Descrição:** Todos os filtros são parâmetros opcionais e podem ser combinados.

* **Exemplo:**

  **Rota:**
      /api/invasions?page=1&pageSize=2

  **Body:**
    ```javascript
    {
      "filters": {
        "state": ["Amazonas"],
        "reserve": ["Andirá-Marau"],
      },
      "enableReserve": true
    }
    ```

* **Resposta:**

    * **Código:** <span style="color:green">**200**</span> <br/>
      **Conteúdo:**

      ```javascript
        {
          "values": [
            {
              "id": "{C15B9FA9-3823-4902-8C87-F171C2B53032}",
              "company": "Falcon Metais Ltda",
              "process": "880816/2008",
              "area": 9928.68,
              "year": 2008,
              "state": "AM",
              "territory": "Andirá-Marau",
              "reservePhase": "Regularizada",
              "reserveEthnicity": "Múra",
              "type": "indigenousLand",
              "miningProcess": "REQUERIMENTO DE PESQUISA",
              "miningProcessType": "miningResearchRequest",
              "substance": "OURO",
              "use": "Industrial",
              "lastEvent": "619 - REQ PESQ/PROCESSO SITUADO EM ÁREA INDÍGENA EM 29/03/2011"
            },
            {
              "id": "{A26AE72A-6395-42ED-817B-179E6EA1D4BC}",
              "company": "Falcon Metais Ltda",
              "process": "880819/2008",
              "area": 9932.87,
              "year": 2008,
              "state": "AM",
              "territory": "Andirá-Marau",
              "reservePhase": "Regularizada",
              "reserveEthnicity": "Múra",
              "type": "indigenousLand",
              "miningProcess": "REQUERIMENTO DE PESQUISA",
              "miningProcessType": "miningResearchRequest",
              "substance": "OURO",
              "use": "Industrial",
              "lastEvent": "157 - REQ PESQ/DESISTÊNCIA REQ PESQ HOMOLOGADA PUB EM 15/04/2021"
            }
          ],
          "pages": 10,
          "results": 20
        }
      ```
      **Descrição:** Retorna um array de objetos contendo os dados de cada requerimento que se enquadra nos filtros definidos, o número de páginas e a quantidade de requerimentos. OBS: Caso o parâmetro output seja definido, o retorno é um arquivo do tipo especificado.
      
    * **Código:** <span style="color:red">**500**</span> <br />
      **Conteúdo:**
      ```javascript
      {
        "message": "Internal Server Error"
      }
      ```
      **Descrição:** Erro interno do servidor.

**Shape dos Requerimentos**
----
Método que retorna os shapes dos requerimentos minerários em Unidades de Conservação e em Terras Indígenas de acordo com os filtros.

* **URL:**
  
      /api/invasions/shape

* **Método:**

  `POST`

* **Parâmetros na URL:**

  Nenhum

* **Parâmetros no Body:**

  ```javascript
  {
    "filters": {
      "state": [], //Array de strings com o nome dos estados
      "company": [], //Array de strings com o nome das empresas
      "reserve": [], //Array de strings com o nome das Terras Indígenas
      "unity": [], //Array de strings com o nome das Unidades de Conservação
      "year": [], //Array de inteiros com os anos
      "substance": [], //Array de strings com o nome das substâncias
      "reservePhase": [], //Array de strings com as fases do processo de homologação das terras indígenas
      "reserveEthnicity": [], //Array de strings com o nome das etinias de terras indígenas
      "requirementPhase": [], //Array de strings com as fases dos requerimentos de mineração
      "use": [], //Array de strings com os usos declarados dos requerimentos de mineração
    },
    "enableUnity": true, //Boolean para ativar/desativar dados de ucs (default: true)
    "enableReserve": true, //Boolean para ativar/desativar dados de Terras Indígenas (default: true)
  }
  ```
  **Descrição:** Todos os filtros são parâmetros opcionais e podem ser combinados.

* **Exemplo:**

  **Body:**
    ```javascript
    {
      "filters": {
        "company": ["Willian Araújo dos Santos"],
        "state": ["Amazonas"],
        "year": [2021],
        "substance": ["MINÉRIO DE ESTANHO"]
      },
      "enableReserve": false
    }
    ```

* **Resposta:**

    * **Código:** <span style="color:green">**200**</span> <br/>
      **Conteúdo:**

      ```javascript
        {
          "reserve": {
            "type": "FeatureCollection",
            "features": []
          },
          "unity": {
            "type": "FeatureCollection",
            "features": [
              {
                "type": "Feature",
                "geometry": {
                  "type": "Polygon",
                  "coordinates": [
                    [
                      [
                        -65.12691752799992,
                        -0.32426850299992793
                      ],
                      ...
                    ]
                  ]
                },
                "properties": {
                  "id": "{A26AE72A-6395-42ED-817B-179E6EA1D4BC}",
                  "company": "Willian Araújo dos Santos",
                  "process": "880084/2021",
                  "area": 176.54,
                  "year": 2021,
                  "state": "AM",
                  "miningProcess": "REQUERIMENTO DE PESQUISA",
                  "miningProcessType": "miningResearchRequest",
                  "territory": "PARQUE NACIONAL DO PICO DA NEBLINA",
                  "type": "protectedArea",
                  "substance": "MINÉRIO DE ESTANHO",
                  "use": "Industrial",
                  "lastEvent": "157 - REQ PESQ/DESISTÊNCIA REQ PESQ HOMOLOGADA PUB EM 15/04/2021"
                }
              },
              ...
            ]
          }
        }
      ```
      **Descrição:** Retorna um objeto que contém os requerimentos em terras indígenas (reserve) e os requerimentos em unidades de conservação (unity) como FeatureCollections.
      
    * **Código:** <span style="color:red">**500**</span> <br />
      **Conteúdo:**
      ```javascript
      {
        "message": "Internal Server Error"
      }
      ```
      **Descrição:** Erro interno do servidor.

**Estatísticas**
----
Método que retorna as estatísticas gerais (número de requerimentos e área total requerida) de Terras Indígenas e Unidades de Conservação de acordo com os filtros.

* **URL:**
  
      /api/statistics

* **Método:**

  `POST`

* **Parâmetros na URL:**

  Nenhum

* **Parâmetros no Body:**

  ```javascript
  {
    "filters": {
      "state": [], //Array de strings com o nome dos estados
      "company": [], //Array de strings com o nome das empresas
      "reserve": [], //Array de strings com o nome das Terras Indígenas
      "unity": [], //Array de strings com o nome das Unidades de Conservação
      "year": [], //Array de inteiros com os anos
      "substance": [], //Array de strings com o nome das substâncias
      "reservePhase": [], //Array de strings com as fases do processo de homologação das terras indígenas
      "reserveEthnicity": [], //Array de strings com o nome das etinias de terras indígenas
      "requirementPhase": [], //Array de strings com as fases dos requerimentos de mineração
      "use": [], //Array de strings com os usos declarados dos requerimentos de mineração
    }
  }
  ```
  **Descrição:** Todos os filtros são parâmetros opcionais e podem ser combinados.

* **Exemplo:**

  **Rota:**
      /api/statistics

  **Body:**
    ```javascript
    {
      "filters": {
        "state": ["Amazonas"],
        "reserve": ["Andirá-Marau"]
      }
    }
    ```

* **Resposta:**

    * **Código:** <span style="color:green">**200**</span> <br/>
      **Conteúdo:**

      ```javascript
        {
          "requirementsIncidence": {
            "reserve": 19,
            "unity": 0,
            "total": 19
          },
          "requiredArea": {
            "reserve": 40742.13,
            "unity": 0,
            "total": 40742.13
          }
        }
      ```
      **Descrição:** Retorna um objeto contendo as estatísticas dos requerimentos que se enquadram nos filtros definidos.
      
    * **Código:** <span style="color:red">**500**</span> <br />
      **Conteúdo:**
      ```javascript
      {
        "message": "Internal Server Error"
      }
      ```
      **Descrição:** Erro interno do servidor.

**Listar Fases do Processo de Homologação das Terras Indígenas**
----
Método que retorna as opções de fase do processo de homologação de terras indígenas.

* **URL:**
  
      /api/reserves/phase

* **Método:**

  `GET`

* **Parâmetros na URL:**

  Nenhum

* **Parâmetros no Body:**

  Nenhum

* **Resposta:**

    * **Código:** <span style="color:green">**200**</span> <br/>
      **Conteúdo:**

      ```javascript
        [
          {
            "type": "reservePhase",
            "value": "Declarada"
          },
          {
            "type": "reservePhase",
            "value": "Delimitada"
          },
          {
            "type": "reservePhase",
            "value": "Em Estudo"
          },
          {
            "type": "reservePhase",
            "value": "Encaminhada RI"
          },
          {
            "type": "reservePhase",
            "value": "Homologada"
          },
          {
            "type": "reservePhase",
            "value": "Regularizada"
          }
        ]
      ```
      **Descrição:** Retorna um array contendo as opções das fases do processo de homologação de terras indígenas.
      
    * **Código:** <span style="color:red">**500**</span> <br />
      **Conteúdo:**
      ```javascript
      {
        "message": "Internal Server Error"
      }
      ```
      **Descrição:** Erro interno do servidor.

**Listar Anos**
----
Método que retorna as opções de anos que contém requerimentos em ucs ou terras indígenas no banco de dados.

* **URL:**
  
      /api/invasions/years

* **Método:**

  `GET`

* **Parâmetros na URL:**

  Nenhum

* **Parâmetros no Body:**

  Nenhum

* **Resposta:**

    * **Código:** <span style="color:green">**200**</span> <br/>
      **Conteúdo:**

      ```javascript
        [
          {
            "type": "year",
            "value": 2017
          },
          {
            "type": "year",
            "value": 2018
          },
          {
            "type": "year",
            "value": 2019
          },
          {
            "type": "year",
            "value": 2020
          },
          {
            "type": "year",
            "value": 2021
          }
        ]
      ```
      **Descrição:** Retorna um array contendo as opções de anos.
      
    * **Código:** <span style="color:red">**500**</span> <br />
      **Conteúdo:**
      ```javascript
      {
        "message": "Internal Server Error"
      }
      ```
      **Descrição:** Erro interno do servidor.

**Listar Fases do Requerimento de Mineração**
----
Método que retorna as opções de fase do requerimento de mineração.

* **URL:**
  
      /api/invasions/phase

* **Método:**

  `GET`

* **Parâmetros na URL:**

  Nenhum

* **Parâmetros no Body:**

  Nenhum

* **Resposta:**

    * **Código:** <span style="color:green">**200**</span> <br/>
      **Conteúdo:**

      ```javascript
        [
          {
            "type": "requirementPhase",
            "value": "APTO PARA DISPONIBILIDADE"
          },
          {
            "type": "requirementPhase",
            "value": "AUTORIZAÇÃO DE PESQUISA"
          },
          {
            "type": "requirementPhase",
            "value": "CONCESSÃO DE LAVRA"
          },
          ...
        ]
      ```
      **Descrição:** Retorna um array contendo as opções das fases dos requerimentos de mineração.
      
    * **Código:** <span style="color:red">**500**</span> <br />
      **Conteúdo:**
      ```javascript
      {
        "message": "Internal Server Error"
      }
      ```
      **Descrição:** Erro interno do servidor.

**Listar Usos do Requerimento de Mineração**
----
Método que retorna as opções de usos dos requerimentos em ucs ou terras indígenas no banco de dados.

* **URL:**
  
      /api/invasions/uses

* **Método:**

  `GET`

* **Parâmetros na URL:**

  Nenhum

* **Parâmetros no Body:**

  Nenhum

* **Resposta:**

    * **Código:** <span style="color:green">**200**</span> <br/>
      **Conteúdo:**

      ```javascript
        [
          {
            "type": "use",
            "value": "Brita"
          },
          {
            "type": "use",
            "value": "Construção civil"
          },
          {
            "type": "use",
            "value": "Engarrafamento"
          },
          {
            "type": "use",
            "value": "Fabricação de cimento"
          },
          {
            "type": "use",
            "value": "Fabricação de ligas"
          },
          {
            "type": "use",
            "value": "Fertilizantes"
          },
          {
            "type": "use",
            "value": "Gema"
          },
          {
            "type": "use",
            "value": "Industrial"
          },
          {
            "type": "use",
            "value": "Metalurgia"
          },
          {
            "type": "use",
            "value": "Não informado"
          },
          {
            "type": "use",
            "value": "Ourivesaria"
          },
          {
            "type": "use",
            "value": "Revestimento"
          }
        ]
      ```
      **Descrição:** Retorna um array contendo as opções de usos.
      
    * **Código:** <span style="color:red">**500**</span> <br />
      **Conteúdo:**
      ```javascript
      {
        "message": "Internal Server Error"
      }
      ```
      **Descrição:** Erro interno do servidor.

**Ranking de frequência e de área**
----
Método que retorna o ranking de acordo com a propiedade e o tipo de dado especificado

* **URL:**
  
      /api/invasions/ranking/:propertyType/:dataType

* **Método:**

  `POST`

* **Parâmetros na URL:**

  - propertyType:[string] - Tipo de propriedade a ser utilizada na construção do ranking ('company', 'state', 'unity', 'reserve', 'ethnicity').
  - dataType:[string] - Tipo de dado a ser retornado, 'requirementsIncidence' para a frequencia de requerimentos em território e 'requiredArea' para área total dos requerimentos por território.
  - page?:[number] - Número da página de registros a ser retornada, retorna a primeira página caso um número não seja informado.
  - sortOrder?[string] - Ordem de ordenação do ranking ('ASC' ou 'DESC'). Default: 'DESC'.

* **Parâmetros no Body:**

  ```javascript
  {
    "filters": {
      "state": [], //Array de strings com o nome dos estados
      "company": [], //Array de strings com o nome das empresas
      "reserve": [], //Array de strings com o nome das Terras Indígenas
      "unity": [], //Array de strings com o nome das Unidades de Conservação
      "year": [], //Array de inteiros com os anos
      "substance": [], //Array de strings com o nome das substâncias
      "reservePhase": [], //Array de strings com as fases do processo de homologação das terras indígenas
      "reserveEthnicity": [], //Array de strings com o nome das etinias de terras indígenas
      "requirementPhase": [], //Array de strings com as fases dos requerimentos de mineração
      "use": [], //Array de strings com os usos declarados dos requerimentos de mineração
    },
    "enableUnity": true, //Boolean para ativar/desativar dados de ucs (default: true)
    "enableReserve": true, //Boolean para ativar/desativar dados de Terras Indígenas (default: true)
  }
  ```

* **Exemplo:**

  **Rota:**
      /api/invasions/ranking/company/requiredArea?page=1

* **Resposta:**

    * **Código:** <span style="color:green">**200**</span> <br/>
      **Conteúdo:**

      ```javascript
        {
          "x": [
            "VALE S.A.",
            "MINERAÇÃO SERRA MORENA LTDA",
            "Iguape Sociedade de Mineração Iguape Ltda",
            "Rio Grande Mineração S A",
            "Mineração Guanhães Ltda"
          ],
          "position": [
            1,
            2,
            3,
            4,
            5
          ],
          "series": [
            {
              "id": "indigenousLand",
              "data": [
                447938.31,
                469529.25,
                446421.21,
                429561.29,
                276058.67
              ]
            },
            {
              "id": "protectedArea",
              "data": [
                112761.6,
                49983.95,
                0,
                7460.83,
                80000
              ]
            }
          ],
          "pageAmount": 125,
          "dataType": "requiredArea"
        }
      ```
      **Descrição:** Retorna um array de series que contém os valores de cada tipo de dado, um array com as respectivas posições e um com os valores da propriedade escolhida. OBS: quando os filtros resultam em um ranking vazio o retorno é null.
      
    * **Código:** <span style="color:red">**500**</span> <br />
      **Conteúdo:**
      ```javascript
      {
        "message": "Internal Server Error"
      }
      ```
      **Descrição:** Erro interno do servidor.

**Health Check**
---
Endpoint que retorna se o servidor está online e a conexão com a base de dados está funcional.

* **URL:**
  
      /api/server/healthz?secret={SECRET}

* **Método:**

  `GET`

* **Parâmetros na URL:**
  
  - secret:[string] =  Chave Secreta. Necessária para impedir acessos anonimos ao teste.