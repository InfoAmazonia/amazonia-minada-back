# Runtime e dependências

O runtime usa Node 24.22.1 LTS e Mongoose 9.11.3, mantendo `strictQuery: true`, `autoCreate: false` e `autoIndex: false` para a conta restrita da aplicação. Os modelos e o contrato da API/CSV permanecem iguais.

Use `npm ci`; package-lock.json é o lockfile de referência. O build Docker compila TypeScript e executa a regressão CSV antes de gerar a imagem com dependências de produção. Execute também os testes operacionais de backup com `python3 -m unittest discover -s ops -p 'test_*.py'`.

Publicar o código no GitHub não altera os contêineres existentes. Para implantar, preserve imagem/Compose anteriores e teste as APIs e os quatro cenários CSV em ambiente isolado antes de substituir o serviço.
