import streamlit as st

from core.session import render_connection_sidebar, get_client

st.set_page_config(
    page_title="Dokku Admin",
    page_icon="🐳",
    layout="wide",
)

render_connection_sidebar()

st.title("🐳 Dokku Admin Panel")
st.caption("Painel administrativo não-oficial para gerenciar um servidor Dokku pelas telas.")

client = get_client()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Visão geral")
    with st.spinner("Consultando aplicações..."):
        apps_result = client.apps_list()

    if apps_result.ok:
        apps = apps_result.lines
        st.metric("Aplicações", len(apps))
        if apps:
            st.dataframe({"App": apps}, width="stretch", hide_index=True)
        else:
            st.info("Nenhuma aplicação encontrada. Crie uma na página **📦 Apps**.")
    else:
        st.error(
            "Não foi possível conectar ao servidor Dokku. "
            "Configure a conexão na barra lateral e clique em **Testar conexão**."
        )
        if apps_result.stderr:
            st.code(apps_result.stderr, language="bash")

with col2:
    st.subheader("Versão do Dokku")
    v = client.version()
    if v.ok:
        st.code(v.stdout, language="bash")
    else:
        st.warning("Versão indisponível (verifique a conexão).")

st.divider()

st.subheader("Navegação")
st.markdown(
    """
Use o menu à esquerda (**pages**) para acessar cada área de gerenciamento:

- **📦 Apps** — criar, renomear, destruir e inspecionar aplicações
- **⚙️ Config** — variáveis de ambiente (`config:set` / `config:unset`)
- **🌐 Domains** — domínios e subdomínios de cada app
- **🔌 Proxy & Ports** — mapeamento de portas do proxy reverso
- **🔒 SSL / Let's Encrypt** — certificados HTTPS
- **📊 Processes** — escalar, reiniciar, parar e reconstruir processos
- **📜 Logs** — logs em tempo real ou histórico das apps
- **🗄️ Databases** — Postgres / MySQL / Redis / Mongo (plugins oficiais)
- **🧩 Plugins** — instalar, remover e listar plugins do Dokku
- **💾 Storage** — volumes persistentes
- **🚀 Deploy** — instruções de deploy via git e rebuild
"""
)

st.divider()
st.caption(
    "⚠️ Este painel executa comandos reais no seu servidor Dokku. "
    "Use com cuidado, especialmente as ações destrutivas (destroy, unmount, etc)."
)
