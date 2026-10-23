# Contas de aplicação com privilégios limitados

A política reproduzível está em `ops/mongodb-application-roles.json`. Os dois
usuários são autenticados no banco `icfj`; nenhum recebe papéis administrativos.

- `minada_backend` / `minadaBackendReader`: apenas `find` nas cinco coleções de
  licenças, UCs, TIs e invasões. Agregações e consultas da API usam essa permissão.
  Sem escrita nem leitura das filas.
- `minada_importer` / `minadaImporter`: leitura das coleções de origem; gravação
  nas duas coleções derivadas e nas quatro filas; criação, inserção, índices e
  descarte nas três coleções temporárias; locks; descarte dos destinos para a
  promoção atômica. Listagem de coleções e renomeação são permissões no `icfj`
  exigidas pelo mecanismo de importação. Sem gestão de usuários, `dropDatabase`,
  leitura administrativa ou acesso a outros bancos.

O importador deve executar a versão com staging/promoção atômica (PR #18 do
monorepo). Um importador legado que apague/inserisse diretamente nas coleções
ativas não é compatível com esta política.

## Provisionamento

Execute primeiro em um MongoDB isolado autenticado e restaurado de backup.
Gere senhas aleatórias distintas de pelo menos 32 caracteres e mantenha um JSON
privado com as chaves `minada_backend` e `minada_importer`. Não use valores de
exemplo em produção. Copie a política, o script e o JSON privado para os caminhos
`/tmp/minada-app-roles.json`, `/tmp/minada-provision.js` e
`/tmp/minada-app-passwords.json` do contêiner MongoDB. O arquivo de senhas deve
ser acessível somente ao administrador (modo 0600).

Execute `ops/provision-mongodb-users.js` com `mongosh --file`, autenticado como
administrador; a senha administrativa deve vir do mecanismo seguro existente.
O script recusa sobrescrever usuários/papéis existentes e não imprime senhas.
Remova o arquivo temporário de senhas do contêiner após provisionar; preserve
apenas uma cópia operacional protegida fora das aplicações.

## Ambientes separados e implantação

O backend passa a ler `./.secrets/backend.env`, com permissão 0600 e diretório 0700.
Esse arquivo contém apenas `MONGO_URI` da conta backend e `HEALTH_SECRET`.
A URI usa `authSource=icfj` e o endereço interno `database:27017`.
O importador usa seu próprio arquivo e conta, conforme a documentação do monorepo.
Não compartilhe o `.env` administrativo com aplicações nem injete a senha root em
outras variáveis. `.secrets` e `.env*` são excluídos do contexto Docker.

Em implantações existentes use Compose >= 2.24.4 e
`docker-compose.application-user.yml`; `!override` remove a lista e o mapa de
ambiente antigos, impedindo que uma URI administrativa sobreponha o novo arquivo.
Atualize também o arquivo base para manter a separação em comandos posteriores.
Publique a imagem testada com `autoCreate: false` e `autoIndex: false`: índices e
coleções permanentes são provisionados operacionalmente, não pela API na inicialização.

Faça backup dos Compose, imagens e ambientes anteriores em diretório privado.
Teste a API completa, CSV e operações positivas/negativas das contas. Publique
um serviço por vez, confirme saúde após a prontidão e confira a identidade e os
privilégios efetivos via `connectionStatus`. Não dispare jobs de publicação como
teste; use filas e dados descartáveis no banco isolado.

A auditoria não destrutiva `ops/verify-mongodb-users.mjs` recebe
`MINADA_BACKEND_URI` e `MINADA_IMPORTER_URI` pelo ambiente privado. Confere consultas,
negação de escrita do backend com filtro impossível, acesso às filas e a outros
bancos. Os testes isolados adicionais devem cobrir importação/indexação/promoção,
filas, negação de criação de usuários, concessão de root e exclusão de banco.

Para reverter, restaure os Compose/imagens/ambientes anteriores e recrie apenas
o serviço afetado. Não restaure dados para reverter credenciais. Essa recuperação
reintroduz temporariamente o acesso administrativo da aplicação; retire-o após
resolver a falha. A conta administrativa continua reservada à operação e backups.
