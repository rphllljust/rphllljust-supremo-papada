Recursos disponíveis
SUAP — Sistema Unificado de Administração Pública (IFRN)

Documentação oficial: https://suap.ifrn.edu.br/comum/documentacao//

Ambiente de teste (treinamento): https://treinamento.suapdevs.ifrn.edu.br/accounts/login/?next=/

Status: disponível (documentação + ambiente de treinamento)

Docker Compose por ambiente

Na raiz do repositório existe o script [scripts/docker-compose-ambiente.ps1](c:/Users/jacja/Documents/github/suap-idep/scripts/docker-compose-ambiente.ps1) para executar os ambientes `development`, `homolog` e `production` com as ações `up`, `rerun`, `down`, `restart` e `ps`.

Ao executar `up` ou `rerun`, o script também roda `bootstrap_initial_admin` dentro do container `backend`. Em `development`, ele executa em seguida o seed acadêmico com `seed_development_data --reset`, deixando o ambiente pronto com alunos, professores, turmas, diários, notas e frequências sem depender do Moodle. Como o bootstrap é idempotente, o administrador inicial so e criado automaticamente quando ainda nao existe naquele banco.

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

Gateway Nginx opcional

Foi adicionada uma sobreposicao opcional para proxy reverso sem alterar os arquivos atuais de ambiente:

```powershell
docker compose -f docker-compose.yml -f docker-compose.homolog.yml -f docker-compose.gateway.yml up -d nginx
```

Arquivo de configuracao:

* `docker/nginx/suap.conf`

Historico escolar digital MEC

Documentacao tecnica detalhada da nova camada (XML/XSD/XMLDSig/PDF/QR/auditoria):

* `SUAP/backend/docs/historico-digital-mec.md`
