import streamlit as st
from core.session import render_connection_sidebar, get_client, show_result

st.set_page_config(page_title="SSL - Dokku Admin", page_icon="🔒", layout="wide")
render_connection_sidebar()
client = get_client()

st.title("🔒 SSL / Let's Encrypt")
st.caption(
    "Requer o plugin `dokku-letsencrypt` instalado no servidor "
    "(`dokku plugin:install https://github.com/dokku/dokku-letsencrypt.git`)."
)

apps_result = client.apps_list()
apps = apps_result.lines if apps_result.ok else []

if not apps:
    st.info("Nenhuma aplicação encontrada. Crie uma na página 📦 Apps.")
    st.stop()

app = st.selectbox("Aplicação", apps)

st.subheader("Certificados configurados")
certs = client.certs_report(app)
if certs.ok:
    st.code(certs.stdout, language="bash")
else:
    st.info("Sem certificado manual configurado ou comando indisponível.")
    if certs.stderr:
        st.code(certs.stderr, language="bash")

st.divider()
st.subheader("Let's Encrypt")

email = st.text_input(
    "E-mail para o Let's Encrypt (opcional, define DOKKU_LETSENCRYPT_EMAIL antes de habilitar)"
)

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🔐 Habilitar Let's Encrypt", type="primary"):
        if email.strip():
            set_result = client.config_set(app, {"DOKKU_LETSENCRYPT_EMAIL": email.strip()}, no_restart=True)
            if not set_result.ok:
                show_result(set_result)
        result = client.letsencrypt_enable(app)
        show_result(result, "Certificado Let's Encrypt emitido/renovado.")

with col2:
    if st.button("🔄 Forçar renovação"):
        show_result(client.letsencrypt_auto_renew(app), "Renovação verificada/aplicada.")

with col3:
    confirm = st.checkbox("Confirmo remover certificado", key="confirm_cert_remove")
    if st.button("🗑️ Remover certificado", disabled=not confirm):
        show_result(client.certs_remove(app), "Certificado removido.")

st.divider()
st.subheader("Todos os certificados Let's Encrypt do servidor")
all_certs = client.letsencrypt_list()
if all_certs.ok:
    st.code(all_certs.stdout or "(nenhum certificado emitido)", language="bash")
else:
    st.warning("Plugin letsencrypt não encontrado ou comando indisponível nesse servidor.")
