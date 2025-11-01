import streamlit as st
import sqlite3
import pandas as pd
from auth.utils import handle_notifications
import plotly.express as px
from datetime import datetime

# Proteção da página
if not st.session_state.get('logged_in'):
    st.error("Você precisa estar logado para acessar esta página.")
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
    # CORREÇÃO: Trocado 'request_id' por 'order_id' e 'approved=1' por "status='aprovado'"
    approved_by_query = """
        SELECT u.username 
        FROM approvals a 
        JOIN users u ON a.user_id = u.id 
        WHERE a.order_id = ? AND a.status = 'aprovado'
    """
    
    # Busca todos os usuários que são aprovadores
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
    """Gera um relatório HTML a partir de um DataFrame."""
    report_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    html = f"""
    <html>
    <head>
        <title>Relatório de Pedidos</title>
        <style>
            body {{ font-family: sans-serif; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ border: 1px solid #dddddd; text-align: left; padding: 8px; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            h1 {{ color: #333; }}
        </style>
    </head>
    <body>
        <h1>Relatório de Pedidos de Compra</h1>
        <p>Gerado em: {report_date}</p>
        {data_frame.to_html(index=False)}
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
