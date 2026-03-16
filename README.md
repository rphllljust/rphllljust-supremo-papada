Recursos disponíveis
SUAP — Sistema Unificado de Administração Pública (IFRN)

Documentação oficial: https://suap.ifrn.edu.br/comum/documentacao//

Ambiente de teste (treinamento): https://treinamento.suapdevs.ifrn.edu.br/accounts/login/?next=/

Status: disponível (documentação + ambiente de treinamento)

Docker Compose por ambiente

Na raiz do repositório existe o script [scripts/docker-compose-ambiente.ps1](c:/Users/jacja/Documents/github/suap-idep/scripts/docker-compose-ambiente.ps1) para executar os ambientes `development`, `homolog` e `production` com as ações `up`, `rerun`, `down`, `restart` e `ps`.

Ao executar `up` ou `rerun`, o script também roda `bootstrap_initial_admin` dentro do container `backend`. Como o comando agora e idempotente, o administrador inicial so e criado automaticamente quando ainda nao existe naquele banco.

Exemplos:

```powershell
.\scripts\docker-compose-ambiente.ps1
.\scripts\docker-compose-ambiente.ps1 -Environment development -Action up
.\scripts\docker-compose-ambiente.ps1 -Environment homolog -Action rerun
.\scripts\docker-compose-ambiente.ps1 -Environment development -Action ps
.\scripts\docker-compose-ambiente.ps1 -Environment development -Action restart
.\scripts\docker-compose-ambiente.ps1 -Environment development -Action down
.\scripts\docker-compose-ambiente.ps1 -Environment production -Action up -NoBuild
```