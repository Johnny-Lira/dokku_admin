import streamlit as st
from core.session import render_connection_sidebar, get_client, show_result

st.set_page_config(page_title="Storage - Dokku Admin", page_icon="💾", layout="wide")
render_connection_sidebar()
client = get_client()

st.title("💾 Storage (volumes persistentes)")

apps_result = client.apps_list()
apps = apps_result.lines if apps_result.ok else []

if not apps:
    st.info("Nenhuma aplicação encontrada. Crie uma na página 📦 Apps.")
    st.stop()

app = st.selectbox("Aplicação", apps)

st.subheader("Volumes montados")
result = client.storage_list(app)
if result.ok:
    st.code(result.stdout or "(nenhum volume montado)", language="bash")
else:
    show_result(result)

st.divider()
st.caption("Formato do mapeamento: `/caminho/no/host:/caminho/no/container`")

col1, col2 = st.columns(2)
with col1:
    st.markdown("**➕ Montar volume**")
    mount_path = st.text_input("Mapeamento", placeholder="/var/lib/dokku/data/storage/minha-app:/data", key="mount")
    if st.button("Montar", type="primary"):
        if mount_path.strip():
            show_result(client.storage_mount(app, mount_path.strip()), "Volume montado. Reinicie a app para aplicar.")
        else:
            st.warning("Informe o mapeamento.")

with col2:
    st.markdown("**➖ Desmontar volume**")
    unmount_path = st.text_input("Mapeamento", placeholder="/var/lib/dokku/data/storage/minha-app:/data", key="unmount")
    if st.button("Desmontar"):
        if unmount_path.strip():
            show_result(client.storage_unmount(app, unmount_path.strip()), "Volume desmontado. Reinicie a app para aplicar.")
        else:
            st.warning("Informe o mapeamento.")

st.info("💡 Após montar/desmontar volumes, use a página **📊 Processes → Restart** para aplicar a mudança.")
