#!/usr/bin/env bash
#
# install.sh - Instala o Dokku Admin Panel diretamente no servidor Dokku,
# rodando como serviço systemd na porta 8501.
#
# Uso:
#   sudo bash install.sh
#
set -euo pipefail

APP_DIR="/opt/dokku-admin"
SERVICE_USER="root"          # precisa rodar como root (ou usuário com acesso ao comando dokku)
SERVICE_NAME="dokku-admin"
PORT="8501"
# Endereço em que o painel escuta. Por padrão, detecta o IP da interface
# WireGuard (wg0) e escuta só nela — nunca na pública. Para sobrescrever:
#   BIND_ADDR=127.0.0.1 sudo bash install.sh
if [[ -z "${BIND_ADDR:-}" ]]; then
  BIND_ADDR="$(ip -4 -o addr show wg0 2>/dev/null | awk '{print $4}' | cut -d/ -f1 | head -n1)"
  BIND_ADDR="${BIND_ADDR:-127.0.0.1}"
fi
ENV_FILE="/etc/dokku-admin.env"

if [[ $EUID -ne 0 ]]; then
  echo "Execute este script como root (sudo bash install.sh)." >&2
  exit 1
fi

if ! command -v dokku >/dev/null 2>&1; then
  echo "AVISO: comando 'dokku' não encontrado neste servidor." >&2
  echo "Este painel foi feito para ser instalado NO servidor Dokku." >&2
fi

echo "==> Copiando arquivos para ${APP_DIR}"
mkdir -p "${APP_DIR}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tar -C "${SCRIPT_DIR}" \
  --exclude=venv --exclude=__pycache__ --exclude='*.pyc' --exclude='.git' --exclude='.env' \
  -cf - . | tar -C "${APP_DIR}" -xf -

echo "==> Criando ambiente virtual Python"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python3 não encontrado. Instale python3 e python3-venv antes de continuar." >&2
  exit 1
fi
python3 -m venv "${APP_DIR}/venv"
"${APP_DIR}/venv/bin/pip" install --upgrade pip
"${APP_DIR}/venv/bin/pip" install -r "${APP_DIR}/requirements.txt"

echo "==> Configurando credenciais de acesso"
if [[ ! -f "${ENV_FILE}" ]]; then
  read -r -p "Usuário do painel [admin]: " ADMIN_USER
  ADMIN_USER="${ADMIN_USER:-admin}"
  read -r -s -p "Senha do painel: " ADMIN_PASS
  echo
  if [[ -z "${ADMIN_PASS}" ]]; then
    echo "Senha vazia não é permitida." >&2
    exit 1
  fi
  umask 077
  cat > "${ENV_FILE}" <<EOF
DOKKU_ADMIN_USER=${ADMIN_USER}
DOKKU_ADMIN_PASSWORD=${ADMIN_PASS}
EOF
  chmod 600 "${ENV_FILE}"
  umask 022
  echo "Credenciais salvas em ${ENV_FILE} (chmod 600)."
else
  echo "Mantendo credenciais existentes em ${ENV_FILE}."
fi

echo "==> Criando serviço systemd"
cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=Dokku Admin Panel (Streamlit)
After=network.target network-online.target wg-quick@wg0.service
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
WorkingDirectory=${APP_DIR}
EnvironmentFile=${ENV_FILE}
ExecStart=${APP_DIR}/venv/bin/streamlit run app.py --server.port=${PORT} --server.address=${BIND_ADDR}
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl restart ${SERVICE_NAME}

echo ""
echo "=================================================================="
echo " Dokku Admin Panel instalado!"
echo " Serviço: systemctl status ${SERVICE_NAME}"
echo " Escutando em: ${BIND_ADDR}:${PORT}"
echo " Login: usuário/senha definidos em ${ENV_FILE}"
echo ""
echo " IMPORTANTE - SEGURANÇA:"
echo " Este painel executa comandos administrativos reais no seu servidor"
echo " Dokku e exige login. Mesmo assim, NÃO exponha a porta ${PORT} na"
echo " internet. Acesso recomendado:"
echo "   - pela interface WireGuard (instale com BIND_ADDR=<IP_WG>), ou"
echo "   - por túnel SSH: ssh -L 8501:${BIND_ADDR}:${PORT} usuario@servidor"
echo "=================================================================="
