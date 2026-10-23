# MongoDB acessível somente por localhost e túnel SSH

O Compose de produção do servidor contém o serviço `database`, acrescentado à
configuração local. Para restringir sua publicação sem mudar imagem, volumes ou
rede interna, use Compose >= 2.24.4 e a sobreposição versionada:

```sh
docker compose -f docker-compose.yml -f docker-compose.mongo-localhost.yml config -q
docker compose -f docker-compose.yml -f docker-compose.mongo-localhost.yml up -d --no-deps --no-build database
```

`!override` substitui a lista de portas inteira: um merge comum pode manter a
publicação anterior em todas as interfaces. O arquivo base da produção também
deve usar `127.0.0.1:27017:27017`, para que uma execução posterior sem a
sobreposição mantenha a restrição. Não aplique esta sobreposição isoladamente:
o arquivo base deve definir a imagem e os volumes existentes do banco.

Antes da mudança, preserve o Compose e a configuração/nomes dos volumes, faça um
`mongodump` e teste sua restauração isolada. Teste a recriação com o novo mapeamento
e a permanência dos volumes antes de aplicar à produção. A alteração recria apenas
o contêiner do MongoDB e causa uma breve interrupção das conexões; não use `down`,
`-v` ou `--renew-anon-volumes`.

Túnel administrativo a partir do computador local:

```sh
ssh -N -L 127.0.0.1:27018:127.0.0.1:27017 root@207.180.233.132
```

Use as opções de chave/known_hosts já configuradas. Conecte o cliente MongoDB a
`127.0.0.1:27018` com autenticação; não coloque a senha na linha de comando ou no
histórico. As aplicações continuam usando `database:27017` pela rede interna.

Após aplicar, confira: mesmas imagem, montagens e IP interno; porta 27017 somente
em 127.0.0.1; bloqueio externo IPv4/IPv6; túnel SSH autenticado; site, APIs e CSV.
Para reverter o mapeamento, restaure o arquivo base e retire a sobreposição do
comando de recriação. Isso reabre o acesso público anterior; use apenas como
recuperação temporária. A reversão de porta não exige restaurar dados.
