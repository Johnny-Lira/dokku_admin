import streamlit as st
from core.session import render_connection_sidebar, get_client, show_result

st.set_page_config(page_title="Apps - Dokku Admin", page_icon="📦", layout="wide")
render_connection_sidebar()
client = get_client()

st.title("📦 Aplicações")

tab_list, tab_create, tab_manage = st.tabs(["Listar", "Criar nova", "Gerenciar"])

with tab_list:
    result = client.apps_list()
    if result.ok:
        apps = result.lines
        if apps:
            st.dataframe({"App": apps}, width="stretch", hide_index=True)
        else:
            st.info("Nenhuma aplicação cadastrada ainda.")
    else:
        show_result(result)

with tab_create:
    with st.form("create_app"):
        name = st.text_input("Nome da nova aplicação", placeholder="minha-app")
        submitted = st.form_submit_button("Criar aplicação", type="primary")
    if submitted:
        if not name.strip():
            st.warning("Informe um nome válido.")
        else:
            result = client.apps_create(name.strip())
            show_result(result, f"Aplicação '{name}' criada com sucesso.")

with tab_manage:
    apps_result = client.apps_list()
    apps = apps_result.lines if apps_result.ok else []

    if not apps:
        st.info("Crie uma aplicação primeiro na aba 'Criar nova'.")
    else:
        selected = st.selectbox("Selecione a aplicação", apps)

        if selected:
            report = client.apps_report(selected)
            with st.expander("📋 Detalhes da aplicação", expanded=True):
                if report.ok:
                    st.code(report.stdout, language="bash")
                else:
                    st.warning("Não foi possível obter o relatório da aplicação.")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Renomear**")
                new_name = st.text_input("Novo nome", key="rename_input")
                if st.button("Renomear aplicação", key="rename_btn"):
                    if new_name.strip():
                        result = client.apps_rename(selected, new_name.strip())
                        show_result(result, "Aplicação renomeada.")
                    else:
                        st.warning("Informe o novo nome.")

            with col2:
                st.markdown("**Bloqueio de deploy**")
                lock_col, unlock_col = st.columns(2)
                if lock_col.button("🔒 Lock", key="lock_btn"):
                    show_result(client.apps_lock(selected), "Aplicação bloqueada para deploys.")
                if unlock_col.button("🔓 Unlock", key="unlock_btn"):
                    show_result(client.apps_unlock(selected), "Aplicação desbloqueada.")

            with col3:
                st.markdown("**Zona de perigo**")
                confirm = st.checkbox(f"Confirmo que quero destruir '{selected}'", key="confirm_destroy")
                if st.button("🗑️ Destruir aplicação", key="destroy_btn", type="primary", disabled=not confirm):
                    result = client.apps_destroy(selected)
                    show_result(result, f"Aplicação '{selected}' destruída.")
                    st.rerun()
