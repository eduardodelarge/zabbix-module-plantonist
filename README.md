# Módulo Zabbix – Plantonista

Consulta, dentro da interface do Zabbix, **quem é o plantonista responsável por uma aplicação em uma data**.
A resposta é apenas o **nome** do plantonista ativo naquela data.

Testado com **Zabbix 7.4**.

---

## Como funciona

```
planilha .xlsx  ──►  importador Python  ──►  tabela plantonista_escala  ──►  módulo de frontend
   (RH/gestão)         (agendado)              (banco do Zabbix)              (Monitoring ▸ Plantonista)
```

- A planilha **não** é lida pelo Zabbix. Um script a converte para uma tabela no banco.
- O módulo apenas consulta essa tabela:

  ```
  plantonista ativo  ⟺  aplicacao = pesquisada
                         AND data_inicio <= data pesquisada
                         AND data_final  >= data pesquisada
  ```
  Em caso de períodos sobrepostos para a mesma aplicação, vale o plantão com `data_inicio` mais recente.

### Colunas esperadas na planilha

| nome | data inicio | data final | celular | aplicação |
|------|-------------|------------|---------|-----------|

O importador aceita variações de nome/acentuação (`data_inicio`, `telefone`, `sistema`, etc.) e datas no formato `dd/mm/aaaa`.

---

## Conteúdo do projeto

```
zabbix-modulo-plantonista/
├── modulo/plantonista/          → o módulo (copiar para o servidor do frontend)
│   ├── manifest.json
│   ├── Module.php
│   ├── actions/PlantonistaList.php
│   └── views/plantonista.list.php
├── sql/
│   ├── schema_mysql.sql
│   ├── schema_postgresql.sql
│   └── teste_consulta.sql
└── importador/
    ├── importar_escala.py
    ├── requirements.txt
    ├── config.example.ini
    └── escala_exemplo.csv
```

---

# Passo a passo de instalação

## 1. Criar a tabela no banco do Zabbix

Descubra qual banco o Zabbix usa (MySQL/MariaDB ou PostgreSQL). A tabela fica **no mesmo banco do Zabbix** (normalmente chamado `zabbix`), porque o módulo usa a conexão do próprio Zabbix.

**MySQL / MariaDB:**
```bash
mysql -u root -p zabbix < sql/schema_mysql.sql
```

**PostgreSQL:**
```bash
psql -U zabbix -d zabbix -f sql/schema_postgresql.sql
```

> Opcional, mas recomendado: descomente no `.sql` a criação do usuário `plantonista_imp` (com permissão só nesta tabela) e use-o no importador em vez do usuário administrativo.

## 2. Preparar o importador da planilha

O importador pode rodar em **qualquer máquina** que tenha:
- acesso de rede ao banco do Zabbix (porta 3306 / 5432);
- acesso à planilha (pasta local, compartilhamento de rede, etc.).

Pode ser a sua máquina Windows, o próprio servidor Zabbix ou um servidor de tarefas.

```bash
cd importador
python -m venv .venv

# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

Crie o `config.ini` a partir do exemplo e ajuste caminho da planilha e string de conexão:

```bash
copy config.example.ini config.ini      # Windows
# cp config.example.ini config.ini      # Linux
```

`config.ini` (exemplo MySQL):
```ini
[planilha]
caminho = C:/Users/eduardo/escala/escala_plantonistas.xlsx
aba =

[banco]
url = mysql+pymysql://plantonista_imp:SUA_SENHA@10.0.0.5:3306/zabbix

[opcoes]
sobreposicao_fatal = false
```

## 3. Primeira importação (teste)

```bash
python importar_escala.py
```

Saída esperada:
```
OK: 12 registro(s) importado(s).
```

Se a planilha tiver problemas (data inválida, coluna faltando, período invertido), o script **aborta e lista as linhas** com erro, sem tocar no banco.

Confira os dados:
```bash
mysql -u root -p zabbix -e "SELECT * FROM plantonista_escala LIMIT 20;"
```
E teste a consulta que o módulo faz (ajuste aplicação/data em `sql/teste_consulta.sql`):
```bash
mysql -u root -p zabbix < sql/teste_consulta.sql
```

## 4. Agendar a importação

A planilha muda com o tempo, então a importação precisa ser recorrente (a cada hora costuma bastar).

**Linux (cron)** – `crontab -e`:
```
*/30 * * * * /caminho/importador/.venv/bin/python /caminho/importador/importar_escala.py >> /var/log/plantonista_import.log 2>&1
```

**Windows (Agendador de Tarefas):**
```powershell
$py  = "C:\Users\eduardo\zabbix-modulo-plantonista\importador\.venv\Scripts\python.exe"
$scr = "C:\Users\eduardo\zabbix-modulo-plantonista\importador\importar_escala.py"
$acao    = New-ScheduledTaskAction -Execute $py -Argument $scr -WorkingDirectory (Split-Path $scr)
$gatilho = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName "Importa escala plantonista" -Action $acao -Trigger $gatilho -RunLevel Highest
```

## 5. Instalar o módulo no Zabbix

O módulo precisa ficar na pasta `modules/` do **frontend** do Zabbix (a máquina que serve a interface web).

1. Localize a pasta de módulos. Caminhos comuns:
   - Pacotes RHEL/Debian: `/usr/share/zabbix/modules/` ou `/usr/share/zabbix/ui/modules/`
   - Instalação por código-fonte: `<raiz-do-frontend>/ui/modules/`

   > O caminho exato aparece na tela **Administration ▸ General ▸ Modules** do seu Zabbix.

2. Copie a pasta `modulo/plantonista/` para lá:
   ```bash
   scp -r modulo/plantonista/ usuario@servidor-web:/tmp/
   ssh usuario@servidor-web 'sudo cp -r /tmp/plantonista /usr/share/zabbix/modules/'
   ```

3. A estrutura final deve ser:
   ```
   /usr/share/zabbix/modules/plantonista/
   ├── manifest.json
   ├── Module.php
   ├── actions/PlantonistaList.php
   └── views/plantonista.list.php
   ```

4. Ajuste permissões (o usuário do servidor web / PHP-FPM precisa **ler** os arquivos):
   ```bash
   sudo chown -R root:root /usr/share/zabbix/modules/plantonista
   sudo chmod -R 644 /usr/share/zabbix/modules/plantonista
   sudo find /usr/share/zabbix/modules/plantonista -type d -exec chmod 755 {} \;
   ```

5. No Zabbix, acesse **Administration ▸ General ▸ Modules** e clique em **Scan directory**.
   O módulo **Plantonista** aparece na lista com status *Disabled*.

6. Clique no status para deixá-lo **Enabled**.

## 6. Usar

Menu **Monitoring ▸ Plantonista**.

- Digite o nome da aplicação (não diferencia maiúsculas/minúsculas).
- Escolha a data (padrão: hoje).
- Clique em **Consultar**.
- A tela mostra o **nome do plantonista** ativo, ou a mensagem de que não há plantonista para aquela aplicação/data.

---

## Atualizações futuras

- **Mudou a escala?** Basta atualizar a planilha; a próxima execução agendada do importador substitui todo o conteúdo da tabela.
- **Mudou o módulo (código)?** Copie os arquivos novos por cima e clique em **Scan directory** de novo (não precisa desabilitar/reabilitar).
- **Desinstalar:** desabilite o módulo em *Modules*, remova a pasta `plantonista/` e, se quiser, `DROP TABLE plantonista_escala;`.

---

## Solução de problemas

| Sintoma | Causa provável / correção |
|---|---|
| Módulo não aparece após *Scan directory* | Pasta no lugar errado, ou `manifest.json` inválido. Confira o caminho em *Modules* e valide o JSON. |
| Erro 403 / "Access denied" ao abrir a tela | Usuário Zabbix com perfil abaixo de *User*. O módulo exige no mínimo *Zabbix User*. |
| "Nenhum plantonista ativo" sempre | Tabela vazia (importador não rodou) ou nome da aplicação diferente do que está na planilha. Rode `sql/teste_consulta.sql`. |
| Importador: `Access denied for user` | Usuário/senha do banco ou GRANT faltando. Veja o bloco de `CREATE USER` no `.sql`. |
| Importador: `Can't connect to MySQL server` | Firewall, `bind-address` do MySQL, ou host/porta errados no `config.ini`. |
| Importador: `colunas ausentes na planilha` | Cabeçalho da planilha diferente. Renomeie as colunas ou acrescente a variação no dicionário `COLMAP` do script. |
| Datas trocadas (mês/dia) | O script assume `dd/mm/aaaa`. Se a planilha usa `mm/dd/aaaa`, ajuste `dayfirst=False` em `importar_escala.py`. |

---
