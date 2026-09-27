import streamlit as st
from core.session import render_connection_sidebar, get_client, show_result

st.set_page_config(page_title="Config - Dokku Admin", page_icon="⚙️", layout="wide")
render_connection_sidebar()
client = get_client()

st.title("⚙️ Variáveis de ambiente (Config)")

apps_result = client.apps_list()
apps = apps_result.lines if apps_result.ok else []

if not apps:
    st.info("Nenhuma aplicação encontrada. Crie uma na página 📦 Apps.")
    st.stop()

app = st.selectbox("Aplicação", apps)
no_restart = st.checkbox("Não reiniciar a aplicação após alterar (--no-restart)", value=False)

st.subheader("Variáveis atuais")
current = client.config_show(app)
if current.ok:
    st.code(current.stdout or "(nenhuma variável definida)", language="bash")
else:
    show_result(current)

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("➕ Definir / atualizar variáveis")
    st.caption("Uma variável por linha, no formato CHAVE=valor")
    text = st.text_area("Variáveis", height=180, placeholder="DATABASE_URL=postgres://...\nDEBUG=false")
    if st.button("Salvar variáveis", type="primary"):
        pairs = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            pairs[k.strip()] = v.strip()
        if not pairs:
            st.warning("Nenhuma variável válida encontrada no texto.")
        else:
            result = client.config_set(app, pairs, no_restart=no_restart)
            show_result(result, f"{len(pairs)} variável(is) definida(s).")

with col2:
    st.subheader("➖ Remover variáveis")
    keys_text = st.text_area("Chaves a remover (uma por linha)", height=180, placeholder="DEBUG\nOLD_KEY")
    if st.button("Remover variáveis"):
        keys = [k.strip() for k in keys_text.splitlines() if k.strip()]
        if not keys:
            st.warning("Informe ao menos uma chave.")
        else:
            result = client.config_unset(app, keys, no_restart=no_restart)
            show_result(result, f"{len(keys)} variável(is) removida(s).")
