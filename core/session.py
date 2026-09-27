"""
core/session.py
Shared sidebar "connection" widget + DokkuClient factory.
Every page calls get_client() to obtain a configured, ready-to-use client,
and render_connection_status() to show the sidebar connection form.
"""

import streamlit as st

from core.auth import logout_button, require_login
from core.dokku_client import DokkuClient

DEFAULTS = {
    "dokku_mode": "local",
    "dokku_host": "",
    "dokku_port": 22,
    "dokku_user": "root",
    "dokku_key_path": "",
    "dokku_password": "",
    "dokku_sudo": False,
}


def _init_state():
    for k, v in DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v


def render_connection_sidebar():
    """Renders the connection settings + status in the sidebar. Call once per page."""
    require_login()
    _init_state()

    with st.sidebar:
        st.markdown("### 🔗 Conexão com o servidor")

        mode = st.radio(
            "Modo de execução",
            options=["local", "ssh"],
            format_func=lambda m: "Local (Streamlit roda no servidor Dokku)" if m == "local" else "Remoto via SSH",
            index=0 if st.session_state["dokku_mode"] == "local" else 1,
            key="dokku_mode_radio",
        )
        st.session_state["dokku_mode"] = mode

        if mode == "ssh":
            st.session_state["dokku_host"] = st.text_input("Host / IP", value=st.session_state["dokku_host"])
            st.session_state["dokku_port"] = st.number_input(
                "Porta SSH", value=int(st.session_state["dokku_port"]), min_value=1, max_value=65535
            )
            st.session_state["dokku_user"] = st.text_input("Usuário SSH", value=st.session_state["dokku_user"])
            auth_mode = st.radio("Autenticação", ["Chave privada", "Senha"], horizontal=True)
            if auth_mode == "Chave privada":
                st.session_state["dokku_key_path"] = st.text_input(
                    "Caminho da chave privada (no servidor onde o Streamlit roda)",
                    value=st.session_state["dokku_key_path"],
                    placeholder="/home/user/.ssh/id_rsa",
                )
                st.session_state["dokku_password"] = ""
            else:
                st.session_state["dokku_password"] = st.text_input(
                    "Senha", value=st.session_state["dokku_password"], type="password"
                )
                st.session_state["dokku_key_path"] = ""
        else:
            st.session_state["dokku_sudo"] = st.checkbox(
                "Executar com sudo",
                value=st.session_state["dokku_sudo"],
                help="Marque se o usuário que roda o Streamlit não for root nem o usuário dokku.",
            )

        col1, col2 = st.columns(2)
        with col1:
            test_clicked = st.button("Testar conexão", width="stretch")
        with col2:
            clear_clicked = st.button("Limpar", width="stretch")

        if clear_clicked:
            for k, v in DEFAULTS.items():
                st.session_state[k] = v
            st.rerun()

        if test_clicked:
            client = get_client()
            result = client.test_connection()
            if result.ok:
                st.success(f"Conectado! {result.stdout.splitlines()[0] if result.stdout else 'OK'}")
            else:
                st.error(f"Falha na conexão: {result.stderr or 'erro desconhecido'}")

        st.divider()
        st.caption(
            "Dica: no modo **local**, instale este painel diretamente no servidor Dokku "
            "(veja o `install.sh`) para não precisar configurar SSH."
        )
        st.divider()
        logout_button()


def get_client() -> DokkuClient:
    _init_state()
    s = st.session_state
    return DokkuClient(
        mode=s["dokku_mode"],
        host=s["dokku_host"] or None,
        port=int(s["dokku_port"]),
        user=s["dokku_user"],
        key_path=s["dokku_key_path"] or None,
        password=s["dokku_password"] or None,
        sudo=s.get("dokku_sudo", False),
    )


def show_result(result, success_msg: str = "Comando executado com sucesso."):
    """Standard way to render a DokkuResult in the UI."""
    if result.ok:
        st.success(success_msg)
        if result.stdout:
            st.code(result.stdout, language="bash")
    else:
        st.error("Erro ao executar o comando.")
        if result.stderr:
            st.code(result.stderr, language="bash")
        if result.stdout:
            st.code(result.stdout, language="bash")
    with st.expander("Ver comando executado"):
        st.code(result.command, language="bash")
