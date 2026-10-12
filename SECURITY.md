# Politica de seguranca

## Dados proibidos no repositorio

- Extratos bancarios reais ou parcialmente anonimizados.
- Nome, CPF, telefone, e-mail, agencia, conta ou identificadores reais.
- Chaves de API, tokens, senhas ou arquivos `.env`.
- Bancos SQLite com transacoes pessoais.
- Notebooks com saidas de execucao ou tabelas reais.

## Processamento privado

Dados reais ficam em `data/` (ignorado pelo Git) localmente, ou no armazenamento
privado do Azure em produção. Testes usam exclusivamente os arquivos fictícios de
`tests/fixtures/`.

O banco SQLite nao possui criptografia propria. Proteja o dispositivo com senha e
criptografia de disco e nunca force a inclusao de `data/` no Git.

Mensagens e extratos enviados ao bot passam pelo Telegram e pelo modelo no Azure AI
Foundry. Os logs registram apenas IDs internos, tipos de evento e codigos de erro,
nunca o conteudo de mensagens ou arquivos.

## Incidente

Se um dado sensivel for versionado:

1. Interrompa novos pushes.
2. Revogue imediatamente qualquer credencial exposta.
3. Remova o dado de todo o historico Git, nao apenas do commit mais recente.
4. Invalide caches e artefatos de CI relacionados.
5. Registre o incidente sem reproduzir o dado sensivel.

Nao abra uma issue publica contendo o dado exposto.
