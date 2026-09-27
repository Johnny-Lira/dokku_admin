import re
import streamlit as st
from core.session import render_connection_sidebar, get_client, show_result

st.set_page_config(page_title="Processes - Dokku Admin", page_icon="📊", layout="wide")
render_connection_sidebar()
client = get_client()

st.title("📊 Processos")

apps_result = client.apps_list()
apps = apps_result.lines if apps_result.ok else []

if not apps:
    st.info("Nenhuma aplicação encontrada. Crie uma na página 📦 Apps.")
    st.stop()

app = st.selectbox("Aplicação", apps)

st.subheader("Status atual dos processos")
report = client.ps_report(app)
if report.ok:
    st.code(report.stdout, language="bash")
else:
    show_result(report)

st.divider()
st.subheader("Ações rápidas")
col1, col2, col3, col4 = st.columns(4)
if col1.button("▶️ Start"):
    show_result(client.ps_start(app), "Aplicação iniciada.")
if col2.button("🔁 Restart"):
    show_result(client.ps_restart(app), "Aplicação reiniciada.")
if col3.button("⏹️ Stop"):
    show_result(client.ps_stop(app), "Aplicação parada.")
if col4.button("🛠️ Rebuild"):
    with st.spinner("Reconstruindo aplicação (pode levar alguns minutos)..."):
        show_result(client.ps_rebuild(app), "Aplicação reconstruída.")

st.divider()
st.subheader("Escalonar processos")
st.caption("Defina quantas instâncias de cada tipo de processo devem rodar. Ex: web=2, worker=1")

text = st.text_area("Um processo por linha, no formato tipo=quantidade", height=120, placeholder="web=2\nworker=1")
if st.button("Aplicar escalonamento", type="primary"):
    counts = {}
    valid = True
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if not re.match(r"^[\w-]+=\d+$", line):
            st.warning(f"Linha inválida ignorada: {line}")
            valid = False
            continue
        proc, qty = line.split("=", 1)
        counts[proc] = qty
    if counts:
        show_result(client.ps_scale(app, counts), "Escalonamento aplicado.")
    elif valid:
        st.warning("Nenhum processo válido informado.")
