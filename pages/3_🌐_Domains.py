import streamlit as st
from core.session import render_connection_sidebar, get_client, show_result

st.set_page_config(page_title="Domains - Dokku Admin", page_icon="🌐", layout="wide")
render_connection_sidebar()
client = get_client()

st.title("🌐 Domínios")

apps_result = client.apps_list()
apps = apps_result.lines if apps_result.ok else []

if not apps:
    st.info("Nenhuma aplicação encontrada. Crie uma na página 📦 Apps.")
    st.stop()

app = st.selectbox("Aplicação", apps)

st.subheader("Domínios configurados")
report = client.domains_report(app)
if report.ok:
    st.code(report.stdout, language="bash")
else:
    show_result(report)

st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**➕ Adicionar domínio**")
    add_domain = st.text_input("Domínio", placeholder="app.meudominio.com", key="add_domain")
    if st.button("Adicionar", key="add_domain_btn"):
        if add_domain.strip():
            show_result(client.domains_add(app, add_domain.strip()), "Domínio adicionado.")
        else:
            st.warning("Informe um domínio.")

with col2:
    st.markdown("**➖ Remover domínio**")
    rm_domain = st.text_input("Domínio", placeholder="app.meudominio.com", key="rm_domain")
    if st.button("Remover", key="rm_domain_btn"):
        if rm_domain.strip():
            show_result(client.domains_remove(app, rm_domain.strip()), "Domínio removido.")
        else:
            st.warning("Informe um domínio.")

with col3:
    st.markdown("**🧹 Limpar todos**")
    confirm = st.checkbox("Confirmo remover todos os domínios", key="confirm_clear_domains")
    if st.button("Limpar domínios", disabled=not confirm):
        show_result(client.domains_clear(app), "Domínios removidos.")

st.divider()
st.subheader("Substituir todos os domínios de uma vez")
set_domains = st.text_area("Um domínio por linha", height=120)
if st.button("Definir domínios (substitui a lista atual)", type="primary"):
    domains = [d.strip() for d in set_domains.splitlines() if d.strip()]
    if domains:
        show_result(client.domains_set(app, domains), "Lista de domínios atualizada.")
    else:
        st.warning("Informe ao menos um domínio.")

st.divider()
st.subheader("Vhost (habilitar/desabilitar)")
col_a, col_b = st.columns(2)
if col_a.button("✅ Habilitar vhost"):
    show_result(client.domains_enable(app), "Vhost habilitado.")
if col_b.button("🚫 Desabilitar vhost"):
    show_result(client.domains_disable(app), "Vhost desabilitado (útil para serviços internos).")
