import streamlit as st
import sqlite3
import pandas as pd
from auth.utils import handle_notifications
import plotly.express as px
from datetime import datetime

# Proteção de acesso à página
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.error("Você precisa estar logado para acessar esta página.")
    st.switch_page("app.py")
    st.stop()

handle_notifications()

st.set_page_config(page_title="Painel de Controle", layout="wide")
st.title("Painel de Controle de Pedidos")

conn = sqlite3.connect('database/compras.db', check_same_thread=False)
cursor = conn.cursor()

# --- Funções de busca no banco de dados ---

def get_all_orders():
    """Busca todos os pedidos."""
    query = "SELECT id, requester, po_number, created_at, total_value, status FROM purchase_orders ORDER BY created_at DESC"
    return pd.read_sql_query(query, conn)

def get_user_orders(user_id):
    """Busca os pedidos de um usuário específico."""
    query = "SELECT id, requester, po_number, created_at, total_value, status FROM purchase_orders WHERE user_id = ? ORDER BY created_at DESC"
    return pd.read_sql_query(query, conn, params=(user_id,))

def get_order_details(order_id):
    """Busca os detalhes e itens de um pedido específico."""
    details_query = "SELECT * FROM purchase_orders WHERE id = ?"
    items_query = "SELECT quantity, unit, description, unit_value, total_value FROM order_items WHERE order_id = ?"
    
    details = pd.read_sql_query(details_query, conn, params=(order_id,))
    items = pd.read_sql_query(items_query, conn, params=(order_id,))
    
    return details.iloc[0] if not details.empty else None, items

def get_approvers_status(order_id):
    """Verifica o status de aprovação para um pedido."""
    approved_by_query = """
        SELECT u.username 
        FROM approvals a 
        JOIN users u ON a.user_id = u.id 
        WHERE a.order_id = ? AND a.status = 'aprovado'
    """
    
    all_approvers_query = "SELECT username FROM users WHERE role = 'aprovador' AND is_active = 1"
    
    approved_list = [row[0] for row in cursor.execute(approved_by_query, (order_id,)).fetchall()]
    all_approvers_list = [row[0] for row in cursor.execute(all_approvers_query).fetchall()]
    
    pending_list = [approver for approver in all_approvers_list if approver not in approved_list]
    
    return approved_list, pending_list

# --- Lógica de exibição ---

user_role = st.session_state.get('role')
user_id = st.session_state.get('user_id')

if user_role == 'Solicitante':
    st.header("Meus Pedidos")
    df_orders = get_user_orders(user_id)
else:
    st.header("Todos os Pedidos")
    df_orders = get_all_orders()

if df_orders.empty:
    st.info("Nenhum pedido encontrado.")
else:
    # --- Gráfico de Pizza ---
    st.subheader("Status dos Pedidos")
    status_counts = df_orders['status'].value_counts().reset_index()
    status_counts.columns = ['status', 'count']
    
    fig = px.pie(status_counts, names='status', values='count', 
                 title='Distribuição de Status dos Pedidos',
                 color='status',
                 color_discrete_map={'pendente':'orange', 'aprovado':'green', 'rejeitado':'red'})
    st.plotly_chart(fig, use_container_width=True)

    # --- Tabela de Pedidos ---
    st.subheader("Lista de Pedidos")
    st.dataframe(df_orders, use_container_width=True)

    # --- Detalhes dos Pedidos Pendentes ---
    st.subheader("Detalhes dos Pedidos Pendentes")
    pending_orders = df_orders[df_orders['status'] == 'pendente']

    if pending_orders.empty:
        st.success("Não há pedidos pendentes de aprovação.")
    else:
        for index, order in pending_orders.iterrows():
            with st.expander(f"Pedido #{order['po_number']} - Solicitante: {order['requester']} - Valor: R$ {order['total_value']:,.2f}"):
                details, items = get_order_details(order['id'])
                if details is not None:
                    st.write("##### Itens do Pedido")
                    st.dataframe(items, use_container_width=True)
                    
                    st.write("##### Justificativa")
                    st.text(details['justification'] or "N/A")

                    st.write("##### Status de Aprovação")
                    approved, pending = get_approvers_status(order['id'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.success("**Aprovado por:**")
                        st.write(", ".join(approved) or "Ninguém ainda")
                    with col2:
                        st.warning("**Pendente de:**")
                        st.write(", ".join(pending) or "N/A")

# --- Geração de Relatório ---
st.divider()
st.header("Relatórios")

def generate_html_report(data_frame):
    """Gera um relatório HTML aprimorado a partir de um DataFrame."""
    report_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    # Métricas de Resumo
    total_orders = len(data_frame)
    total_value = data_frame['total_value'].sum()
    status_counts = data_frame['status'].value_counts()
    
    # Tabela de dados com estilo
    df_html = data_frame.to_html(index=False, justify='center', border=0).replace(
        '<table', '<table style="width:100%; border-collapse: collapse; font-family: Arial, sans-serif;"'
    ).replace(
        '<thead>', '<thead style="background-color: #f2f2f2;">'
    ).replace(
        '<th>', '<th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">'
    ).replace(
        '<td>', '<td style="padding: 12px; text-align: left; border-bottom: 1px solid #ddd;">'
    )

    html = f"""
    <html>
    <head>
        <title>Relatório de Pedidos de Compra</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; color: #333; }}
            .container {{ max-width: 1200px; margin: 20px auto; padding: 20px; background-color: #fff; box-shadow: 0 0 10px rgba(0,0,0,0.1); border-radius: 8px; }}
            h1, h2 {{ color: #0056b3; }}
            h1 {{ text-align: center; border-bottom: 2px solid #0056b3; padding-bottom: 10px; }}
            .summary {{ display: flex; justify-content: space-around; text-align: center; margin: 20px 0; padding: 20px; background-color: #eef; border-radius: 8px; }}
            .metric {{ flex: 1; }}
            .metric h3 {{ margin: 0; font-size: 1.2em; color: #555; }}
            .metric p {{ margin: 5px 0 0; font-size: 2em; font-weight: bold; color: #0056b3; }}
            .footer {{ text-align: center; margin-top: 20px; font-size: 0.9em; color: #777; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Relatório de Pedidos de Compra</h1>
            <p class="footer">Gerado em: {report_date}</p>

            <h2>Resumo Geral</h2>
            <div class="summary">
                <div class="metric">
                    <h3>Total de Pedidos</h3>
                    <p>{total_orders}</p>
                </div>
                <div class="metric">
                    <h3>Valor Total</h3>
                    <p>R$ {total_value:,.2f}</p>
                </div>
                <div class="metric">
                    <h3>Pedidos Pendentes</h3>
                    <p>{status_counts.get('pendente', 0)}</p>
                </div>
                <div class="metric">
                    <h3>Pedidos Aprovados</h3>
                    <p>{status_counts.get('aprovado', 0)}</p>
                </div>
                 <div class="metric">
                    <h3>Pedidos Rejeitados</h3>
                    <p>{status_counts.get('rejeitado', 0)}</p>
                </div>
            </div>

            <h2>Detalhes dos Pedidos</h2>
            {df_html}
            
            <div class="footer">
                <p>&copy; {datetime.now().year} - Sistema de Solicitação de Compras</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

if not df_orders.empty:
    report_html = generate_html_report(df_orders)
    st.download_button(
        label="Baixar Relatório Detalhado (HTML)",
        data=report_html,
        file_name="relatorio_pedidos.html",
        mime="text/html"
    )
else:
    st.info("Não há dados para gerar um relatório.")


# Botão de Sair na barra lateral
if st.sidebar.button("Sair"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.switch_page("app.py")
