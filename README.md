# 🐳 Dokku Admin Panel

Painel administrativo web (não-oficial), feito em Python + Streamlit, para gerenciar um
servidor [Dokku](https://dokku.com/docs/) pelas telas, sem precisar digitar comandos no
terminal a cada operação.

Cobre as principais áreas administrativas do Dokku:

- **Apps** — criar, renomear, destruir, `apps:report`, lock/unlock
- **Config** — variáveis de ambiente (`config:set` / `config:unset`)
- **Domains** — domínios/subdomínios por app
- **Proxy & Ports** — mapeamento de portas do proxy reverso (nginx)
- **SSL / Let's Encrypt** — emissão e renovação de certificados
- **Processes** — start/stop/restart/rebuild e `ps:scale`
- **Logs** — visualização de logs por app/processo
- **Databases** — Postgres, MySQL, Redis, Mongo (plugins oficiais): create, link, unlink, destroy, logs
- **Plugins** — instalar/remover/listar plugins do Dokku
- **Storage** — montar/desmontar volumes persistentes
- **Deploy** — instruções de `git push` + rebuild manual

## Como funciona

O painel simplesmente monta e executa comandos `dokku ...` reais, capturando a saída e
exibindo na tela. Ele pode rodar de duas formas:

1. **Local** (recomendado): o Streamlit roda *no próprio servidor Dokku* e executa os
   comandos via `subprocess`, como se você tivesse aberto um terminal ali.
2. **SSH remoto**: o Streamlit roda em outra máquina (seu notebook, por exemplo) e se
   conecta ao servidor Dokku via SSH (usando `paramiko`) para executar os comandos.

Você escolhe o modo na barra lateral, dentro do próprio app.

## Instalação rápida (no servidor Dokku)

```bash
# no servidor, com o Dokku já instalado
git clone <este-repositorio-ou-copie-os-arquivos> dokku-admin
cd dokku-admin
sudo bash install.sh
```

O bind é detectado automaticamente na interface WireGuard `wg0` (fallback
`127.0.0.1`; sobrescreva com `BIND_ADDR=... sudo bash install.sh`).

Na primeira execução o script pede usuário e senha e grava em
`/etc/dokku-admin.env` (permissão `600`). Cria um serviço systemd de mesmo nome
na porta `8501`.

```bash
systemctl status dokku-admin
```

Acesse (dentro da VPN): `http://<IP_DA_INTERFACE_WIREGUARD>:8501`

Variáveis aceitas no install: `BIND_ADDR` (default `127.0.0.1`), `PORT`
(default `8501`). Para trocar a senha depois, edite `/etc/dokku-admin.env` e
rode `systemctl restart dokku-admin`.

## Instalação manual / rodando localmente (modo SSH)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edite usuário/senha do login
streamlit run app.py   # http://127.0.0.1:8502
```

O login é lido do `.env` na raiz do projeto (veja `.env.example`). Variáveis de
ambiente reais têm prioridade sobre o `.env`.

Depois, na barra lateral, escolha **Remoto via SSH** e informe host, usuário e chave/senha.

## ⚠️ Segurança — leia antes de expor

Este painel executa comandos administrativos reais, incluindo ações destrutivas
(`apps:destroy`, `*:destroy`, `storage:unmount`, etc). Ele tem **login próprio**
(usuário/senha, fail-closed) e deve rodar **apenas dentro da VPN/WireGuard**:

- O bind é detectado na interface WireGuard `wg0` — nunca `0.0.0.0`. Ajuste manual
  via `BIND_ADDR` se sua interface tiver outro nome;
- O login fica em `/etc/dokku-admin.env` (`600`, somente root). Sem essas variáveis o
  painel recusa todo acesso;
- Alternativa sem WireGuard: túnel SSH
  `ssh -L 8501:127.0.0.1:8501 usuario@servidor`;
- Se rodar em modo SSH, prefira autenticação por chave privada em vez de senha (a chave
  do host é validada contra o `known_hosts`, sem `AutoAddPolicy`).

## Requisitos

- Python 3.9+
- Dokku instalado no servidor-alvo
- Se usar modo SSH: usuário com permissão de executar `dokku` no servidor
  (usuário `dokku` ou `root`, ou um usuário com `sudo` configurado — veja a opção
  "Executar com sudo" no modo local)

## Estrutura do projeto

```
dokku_admin/
├── app.py                     # dashboard principal
├── core/
│   ├── auth.py                # login/senha (fail-closed)
│   ├── dokku_client.py        # executa comandos dokku (local/SSH)
│   └── session.py             # sidebar de conexão + helpers de UI
├── pages/
│   ├── 1_📦_Apps.py
│   ├── 2_⚙️_Config.py
│   ├── 3_🌐_Domains.py
│   ├── 4_🔌_Proxy_Ports.py
│   ├── 5_🔒_SSL.py
│   ├── 6_📊_Processes.py
│   ├── 7_📜_Logs.py
│   ├── 8_🗄️_Databases.py
│   ├── 9_🧩_Plugins.py
│   ├── 10_💾_Storage.py
│   └── 11_🚀_Deploy.py
├── requirements.txt
├── install.sh
└── README.md
```

## Referência

Baseado na documentação oficial do Dokku: <https://dokku.com/docs/> (código-fonte dos
docs em <https://github.com/dokku/dokku/tree/master/docs>).
