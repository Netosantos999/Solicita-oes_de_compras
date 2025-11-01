import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from auth.utils import handle_notifications
from datetime import datetime

# Proteção de segurança e verificação de notificações
if not st.session_state.get('logged_in'):
    st.error("Por favor, faça o login primeiro.")
    st.switch_page("app.py")
    st.stop()

handle_notifications()

st.set_page_config(page_title="Painel de Controle", layout="wide")

def generate_html_report(orders_df, conn):
    """Gera uma string HTML contendo o relatório detalhado dos pedidos."""
    
    # Estilos CSS para o relatório
    styles = """
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .report-header { text-align: center; border-bottom: 2px solid #ccc; padding-bottom: 10px; }
        .order-container { border: 1px solid #ddd; border-radius: 8px; margin-bottom: 20px; padding: 15px; background-color: #f9f9f9; }
        .order-title { color: #333; border-bottom: 1px solid #eee; padding-bottom: 5px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .success { color: green; }
        .warning { color: orange; }
    </style>
    """
    
    html = f"<html><head><title>Relatório de Pedidos</title>{styles}</head><body>"
    html += f"<div class='report-header'><h1>Relatório de Pedidos de Compra</h1><p>Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p></div>"

    all_approvers_list = pd.read_sql_query("SELECT username FROM users WHERE role = 'aprovador'", conn)['username'].tolist()

    for _, order in orders_df.iterrows():
        html += "<div class='order-container'>"
        html += f"<h2 class='order-title'>Pedido #{order['id']} - Status: {order['status'].upper()}</h2>"
        html += f"<p><b>Solicitante:</b> {order['requester']}</p>"
        html += f"<p><b>Valor Total:</b> R$ {order['total_value']:,.2f}</p>"
        html += f"<p><b>Justificativa:</b> {order['justification']}</p>"

        # Tabela de Itens
        items_df = pd.read_sql_query(f"SELECT quantity, unit, description, unit_value, total_value FROM order_items WHERE order_id = {order['id']}", conn)
        html += "<h3>Itens do Pedido</h3>"
        html += "<table><tr><th>Qtde</th><th>Unidade</th><th>Descrição</th><th>Valor Un.</th><th>Valor Total</th></tr>"
        for _, item in items_df.iterrows():
            html += f"<tr><td>{item['quantity']}</td><td>{item['unit']}</td><td>{item['description']}</td><td>R$ {item['unit_value']:,.2f}</td><td>R$ {item['total_value']:,.2f}</td></tr>"
        html += "</table>"

        # Status de Aprovação
        if order['status'] == 'pendente':
            html += "<h3>Análise de Aprovações</h3>"
            approved_by_df = pd.read_sql_query(f"SELECT u.username FROM approvals a JOIN users u ON a.user_id = u.id WHERE a.request_id = {order['id']} AND a.approved = 1", conn)
            approved_by_list = approved_by_df['username'].tolist()
            pending_approvers = [p for p in all_approvers_list if p not in approved_by_list]
            
            if approved_by_list:
                html += f"<p class='success'><b>Já aprovado por:</b> {', '.join(approved_by_list)}</p>"
            if pending_approvers:
                html += f"<p class='warning'><b>Aguardando aprovação de:</b> {', '.join(pending_approvers)}</p>"
        
        html += "</div>"

    html += "</body></html>"
    return html

# --- Lógica de Título e Consulta ---
user_role = st.session_state.get('role')
user_id = st.session_state.get('user_id')

if user_role == 'Solicitante':
    st.title("Meus Pedidos Enviados")
    query = "SELECT * FROM purchase_orders WHERE user_id = ? ORDER BY id DESC"
    params = (user_id,)
else:
    st.title("Painel de Controle de Pedidos")
    query = "SELECT * FROM purchase_orders ORDER BY id DESC"
    params = ()

# --- Exibição dos Dados ---
try:
    conn = sqlite3.connect('database/compras.db')
    all_orders_df = pd.read_sql_query(query, conn, params=params)

    if all_orders_df.empty:
        st.info("Nenhum pedido encontrado.")
    else:
        # --- Botão de Download ---
        st.subheader("Exportar Relatório")
        html_report = generate_html_report(all_orders_df, conn)
        st.download_button(
            label="📥 Baixar Relatório Detalhado (HTML)",
            data=html_report,
            file_name="relatorio_pedidos.html",
            mime="text/html",
            use_container_width=True
        )

        # --- Gráfico de Pizza ---
        st.subheader("Status Geral dos Pedidos")
        status_counts = all_orders_df['status'].value_counts().reset_index()
        status_counts.columns = ['status', 'count']
        
        fig = px.pie(
            status_counts, 
            names='status', 
            values='count', 
            title='Distribuição de Status dos Pedidos',
            color='status',
            color_discrete_map={'pendente':'orange', 'aprovado':'green', 'reprovado':'red'}
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- Relatório Detalhado na Página ---
        st.subheader("Lista de Pedidos")
        all_approvers_df = pd.read_sql_query("SELECT username FROM users WHERE role = 'aprovador'", conn)
        all_approvers_list = all_approvers_df['username'].tolist()

        for index, order in all_orders_df.iterrows():
            with st.expander(f"Pedido #{order['id']} - {order['requester']} - Valor: R$ {order['total_value']:,.2f} - Status: {order['status'].upper()}"):
                st.markdown(f"**Nº Pedido (interno):** {order['po_number']}")
                st.markdown(f"**Justificativa:** {order['justification']}")
                
                if order['status'] == 'pendente':
                    st.markdown("---")
                    st.markdown("**Análise de Aprovações:**")
                    approved_by_df = pd.read_sql_query(f"SELECT u.username FROM approvals a JOIN users u ON a.user_id = u.id WHERE a.request_id = {order['id']} AND a.approved = 1", conn)
                    approved_by_list = approved_by_df['username'].tolist()
                    pending_approvers = [p for p in all_approvers_list if p not in approved_by_list]

                    if approved_by_list:
                        st.success(f"**Já aprovado por:** {', '.join(approved_by_list)}")
                    if pending_approvers:
                        st.warning(f"**Aguardando aprovação de:** {', '.join(pending_approvers)}")
                    else:
                        st.info("Todos os aprovadores já registraram seu voto.")

    conn.close()

except Exception as e:
    st.error(f"Não foi possível carregar o painel de controle: {e}")

# Botão de Sair na barra lateral
if st.sidebar.button("Sair"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.switch_page("app.py")
