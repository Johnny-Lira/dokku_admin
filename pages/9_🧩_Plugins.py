import streamlit as st
from core.session import render_connection_sidebar, get_client, show_result

st.set_page_config(page_title="Plugins - Dokku Admin", page_icon="🧩", layout="wide")
render_connection_sidebar()
client = get_client()

st.title("🧩 Plugins")

st.subheader("Plugins instalados")
result = client.plugin_list()
if result.ok:
    st.code(result.stdout, language="bash")
else:
    show_result(result)

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("➕ Instalar plugin")
    url = st.text_input("URL do repositório git do plugin", placeholder="https://github.com/dokku/dokku-postgres.git")
    plugin_name = st.text_input("Nome customizado (opcional)")
    if st.button("Instalar plugin", type="primary"):
        if url.strip():
            with st.spinner("Instalando plugin..."):
                res = client.plugin_install(url.strip(), plugin_name.strip() or None)
            show_result(res, "Plugin instalado.")
        else:
            st.warning("Informe a URL do plugin.")

with col2:
    st.subheader("➖ Remover plugin")
    remove_name = st.text_input("Nome do plugin a remover", placeholder="postgres")
    confirm = st.checkbox("Confirmo remover este plugin")
    if st.button("Remover plugin", disabled=not confirm):
        if remove_name.strip():
            show_result(client.plugin_uninstall(remove_name.strip()), "Plugin removido.")
        else:
            st.warning("Informe o nome do plugin.")

st.divider()
st.subheader("Plugins oficiais populares")
st.markdown(
    """
| Plugin | URL |
|---|---|
| Postgres | `https://github.com/dokku/dokku-postgres.git` |
| MySQL | `https://github.com/dokku/dokku-mysql.git` |
| Redis | `https://github.com/dokku/dokku-redis.git` |
| MongoDB | `https://github.com/dokku/dokku-mongo.git` |
| Let's Encrypt | `https://github.com/dokku/dokku-letsencrypt.git` |
| Redirect (www → apex etc.) | `https://github.com/dokku/dokku-redirect.git` |
"""
)
