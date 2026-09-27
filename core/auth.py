"""
core/auth.py
Login simples (usuário/senha) para o painel.

As credenciais vêm das variáveis de ambiente DOKKU_ADMIN_USER e
DOKKU_ADMIN_PASSWORD (definidas pelo install.sh em /etc/dokku-admin.env).

Fail-closed: sem credencial configurada, ninguém entra.
"""

from __future__ import annotations

import hmac
import os
from pathlib import Path
from typing import Optional, Tuple

USER_ENV = "DOKKU_ADMIN_USER"
PASSWORD_ENV = "DOKKU_ADMIN_PASSWORD"

_DOTENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def _load_dotenv() -> None:
    """Carrega .env da raiz do projeto. Variáveis já no ambiente têm prioridade."""
    if not _DOTENV_PATH.is_file():
        return
    for line in _DOTENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip().removeprefix("export ").strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()


def get_credentials() -> Optional[Tuple[str, str]]:
    """Retorna (usuário, senha) ou None se não configurado."""
    user = os.environ.get(USER_ENV)
    password = os.environ.get(PASSWORD_ENV)
    if user and password:
        return user, password
    return None


def verify(user: str, password: str) -> bool:
    """Compara em tempo constante. Falha se não houver credencial configurada."""
    creds = get_credentials()
    if creds is None:
        return False
    expected_user, expected_password = creds
    user_ok = hmac.compare_digest(user.encode(), expected_user.encode())
    pass_ok = hmac.compare_digest(password.encode(), expected_password.encode())
    return user_ok and pass_ok


def require_login() -> None:
    """Renderiza a tela de login e para a execução da página até autenticar."""
    import streamlit as st

    if st.session_state.get("authenticated"):
        return

    if get_credentials() is None:
        st.title("🔐 Dokku Admin")
        st.error(
            f"Login não configurado. Defina {USER_ENV} e {PASSWORD_ENV} no ambiente "
            "do serviço (veja o install.sh)."
        )
        st.stop()

    st.title("🔐 Dokku Admin")
    st.caption("Acesso restrito. Informe usuário e senha para continuar.")

    with st.form("login_form"):
        user = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar", type="primary")

    if submitted:
        if verify(user, password):
            st.session_state["authenticated"] = True
            st.session_state["auth_user"] = user
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

    st.stop()


def logout_button() -> None:
    """Botão de sair. Deve ser chamado dentro do contexto da sidebar."""
    import streamlit as st

    st.caption(f"Logado como **{st.session_state.get('auth_user', '?')}**")
    if st.button("Sair", width="stretch"):
        st.session_state["authenticated"] = False
        st.session_state.pop("auth_user", None)
        st.rerun()
