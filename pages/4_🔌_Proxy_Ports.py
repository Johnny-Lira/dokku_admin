import streamlit as st
from core.session import render_connection_sidebar, get_client, show_result

st.set_page_config(page_title="Proxy & Ports - Dokku Admin", page_icon="🔌", layout="wide")
render_connection_sidebar()
client = get_client()

st.title("🔌 Proxy & Portas")

apps_result = client.apps_list()
apps = apps_result.lines if apps_result.ok else []

if not apps:
    st.info("Nenhuma aplicação encontrada. Crie uma na página 📦 Apps.")
    st.stop()

app = st.selectbox("Aplicação", apps)

st.subheader("Configuração atual do proxy")
report = client.proxy_report(app)
if report.ok:
    st.code(report.stdout, language="bash")
else:
    show_result(report)

st.divider()
st.subheader("Mapeamento de portas")
st.caption("Formato: `scheme:host_port:container_port` — ex: `http:80:5000` ou `https:443:5000`")

col1, col2 = st.columns(2)
with col1:
    st.markdown("**➕ Adicionar mapeamento**")
    add_mapping = st.text_input("Mapeamento", placeholder="http:80:5000", key="add_mapping")
    if st.button("Adicionar mapeamento"):
        if add_mapping.strip():
            show_result(client.proxy_ports_add(app, add_mapping.strip()), "Mapeamento adicionado.")
        else:
            st.warning("Informe um mapeamento válido.")

with col2:
    st.markdown("**➖ Remover mapeamento**")
    rm_mapping = st.text_input("Mapeamento", placeholder="http:80:5000", key="rm_mapping")
    if st.button("Remover mapeamento"):
        if rm_mapping.strip():
            show_result(client.proxy_ports_remove(app, rm_mapping.strip()), "Mapeamento removido.")
        else:
            st.warning("Informe um mapeamento válido.")

st.markdown("**🔁 Substituir todos os mapeamentos**")
set_mappings = st.text_area("Um mapeamento por linha", height=100, placeholder="http:80:5000\nhttps:443:5000")
if st.button("Definir mapeamentos (substitui os atuais)", type="primary"):
    mappings = [m.strip() for m in set_mappings.splitlines() if m.strip()]
    if mappings:
        show_result(client.proxy_ports_set(app, mappings), "Mapeamentos atualizados.")
    else:
        st.warning("Informe ao menos um mapeamento.")

st.divider()
st.subheader("Proxy reverso (nginx)")
col_a, col_b = st.columns(2)
if col_a.button("✅ Habilitar proxy"):
    show_result(client.proxy_enable(app), "Proxy habilitado.")
if col_b.button("🚫 Desabilitar proxy"):
    show_result(
        client.proxy_disable(app),
        "Proxy desabilitado — a app passa a expor a porta diretamente do container.",
    )
