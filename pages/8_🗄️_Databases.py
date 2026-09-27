import streamlit as st
from core.session import render_connection_sidebar, get_client, show_result

st.set_page_config(page_title="Databases - Dokku Admin", page_icon="🗄️", layout="wide")
render_connection_sidebar()
client = get_client()

st.title("🗄️ Bancos de dados (plugins oficiais)")
st.caption(
    "Requer os plugins correspondentes instalados, ex: "
    "`dokku plugin:install https://github.com/dokku/dokku-postgres.git`"
)

service = st.selectbox("Serviço", ["postgres", "mysql", "redis", "mongo"])

apps_result = client.apps_list()
apps = apps_result.lines if apps_result.ok else []

tab_list, tab_create, tab_manage = st.tabs(["Listar", "Criar", "Gerenciar / Vincular"])

with tab_list:
    result = client.service_list(service)
    if result.ok:
        st.code(result.stdout or f"(nenhum serviço {service} criado)", language="bash")
    else:
        st.warning(f"Plugin '{service}' não encontrado ou comando indisponível.")
        if result.stderr:
            st.code(result.stderr, language="bash")

with tab_create:
    with st.form("create_service"):
        db_name = st.text_input("Nome do serviço", placeholder=f"minha-app-{service}")
        extra = st.text_input(
            "Argumentos extras (opcional)",
            placeholder="--image postgres --image-version 16",
            help="Flags extras aceitas pelo comando <service>:create, separadas por espaço.",
        )
        submitted = st.form_submit_button("Criar serviço", type="primary")
    if submitted:
        if db_name.strip():
            extra_args = extra.split() if extra.strip() else None
            result = client.service_create(service, db_name.strip(), extra_args)
            show_result(result, f"Serviço {service} '{db_name}' criado.")
        else:
            st.warning("Informe um nome para o serviço.")

with tab_manage:
    list_result = client.service_list(service)
    services = list_result.lines if list_result.ok else []
    # dokku *:list pode imprimir um cabeçalho "=====> ..." ou "NAME"
    services = [s for s in services if s and s.split()[0].lower() != "name"]

    if not services:
        st.info(f"Nenhum serviço {service} disponível ainda.")
    else:
        db_name = st.selectbox("Serviço", services)

        info = client.service_info(service, db_name)
        with st.expander("📋 Informações do serviço", expanded=True):
            if info.ok:
                st.code(info.stdout, language="bash")
            else:
                show_result(info)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🔗 Vincular a uma aplicação**")
            app_to_link = st.selectbox("Aplicação", apps, key="link_app") if apps else None
            if st.button("Vincular", key="link_btn") and app_to_link:
                show_result(
                    client.service_link(service, db_name, app_to_link),
                    f"'{db_name}' vinculado a '{app_to_link}'.",
                )

            st.markdown("**⛓️‍💥 Desvincular de uma aplicação**")
            app_to_unlink = st.selectbox("Aplicação", apps, key="unlink_app") if apps else None
            if st.button("Desvincular", key="unlink_btn") and app_to_unlink:
                show_result(
                    client.service_unlink(service, db_name, app_to_unlink),
                    f"'{db_name}' desvinculado de '{app_to_unlink}'.",
                )

        with col2:
            st.markdown("**⏯️ Controle do serviço**")
            c1, c2 = st.columns(2)
            if c1.button("▶️ Start", key="svc_start"):
                show_result(client.service_start(service, db_name), "Serviço iniciado.")
            if c2.button("⏹️ Stop", key="svc_stop"):
                show_result(client.service_stop(service, db_name), "Serviço parado.")

            st.markdown("**🗑️ Zona de perigo**")
            confirm = st.checkbox(f"Confirmo destruir '{db_name}'", key="confirm_svc_destroy")
            if st.button("Destruir serviço", disabled=not confirm, type="primary"):
                show_result(client.service_destroy(service, db_name), "Serviço destruído.")
                st.rerun()

        st.divider()
        st.markdown("**📜 Logs do serviço**")
        if st.button("Buscar logs do serviço"):
            logs = client.service_logs(service, db_name)
            if logs.ok:
                st.code(logs.stdout or "(sem logs)", language="log")
            else:
                show_result(logs)
