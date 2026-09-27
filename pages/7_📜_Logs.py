import streamlit as st
from core.session import render_connection_sidebar, get_client

st.set_page_config(page_title="Logs - Dokku Admin", page_icon="📜", layout="wide")
render_connection_sidebar()
client = get_client()

st.title("📜 Logs")

apps_result = client.apps_list()
apps = apps_result.lines if apps_result.ok else []

if not apps:
    st.info("Nenhuma aplicação encontrada. Crie uma na página 📦 Apps.")
    st.stop()

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    app = st.selectbox("Aplicação", apps)
with col2:
    num = st.number_input("Nº de linhas", min_value=10, max_value=5000, value=200, step=10)
with col3:
    process = st.text_input("Processo (opcional)", placeholder="web")

if st.button("🔄 Buscar logs", type="primary"):
    with st.spinner("Buscando logs..."):
        result = client.logs(app, num=int(num), process=process.strip() or None)
    if result.ok:
        st.code(result.stdout or "(sem logs)", language="log")
    else:
        st.error("Erro ao buscar logs.")
        if result.stderr:
            st.code(result.stderr, language="bash")

st.caption(
    "Para acompanhar logs em tempo real (`dokku logs -t`), use o terminal — "
    "o Streamlit não suporta streams infinitos de forma nativa."
)
