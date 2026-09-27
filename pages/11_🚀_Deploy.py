import streamlit as st
from core.session import render_connection_sidebar, get_client, show_result

st.set_page_config(page_title="Deploy - Dokku Admin", page_icon="🚀", layout="wide")
render_connection_sidebar()
client = get_client()

st.title("🚀 Deploy")

apps_result = client.apps_list()
apps = apps_result.lines if apps_result.ok else []

if not apps:
    st.info("Nenhuma aplicação encontrada. Crie uma na página 📦 Apps.")
    st.stop()

app = st.selectbox("Aplicação", apps)

host = st.session_state.get("dokku_host") or "SEU_SERVIDOR"
ssh_user = "dokku"

st.subheader("Como fazer deploy desta aplicação")
st.markdown(
    "O Dokku funciona por **git push**: o próprio push para o servidor dispara o build e o deploy."
)
st.code(
    f"""# 1. Adicione o remoto git do Dokku no seu projeto local
git remote add dokku {ssh_user}@{host}:{app}

# 2. Envie o código (branch main ou master, conforme seu repositório)
git push dokku main
""",
    language="bash",
)

st.divider()
st.subheader("Rebuild manual (sem novo push)")
st.caption("Reconstrói a imagem a partir do último release, útil após mudar variáveis de ambiente ou storage.")
if st.button("🛠️ Rebuild agora", type="primary"):
    with st.spinner("Reconstruindo..."):
        result = client.ps_rebuild(app)
    show_result(result, "Deploy reconstruído com sucesso.")

st.divider()
st.subheader("Relatório completo da aplicação")
report = client.apps_report(app)
if report.ok:
    st.code(report.stdout, language="bash")
else:
    show_result(report)
