import streamlit as st
import sqlite3
import pandas as pd
from auth.utils import handle_notifications

# Proteção de acesso à página
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.error("Você precisa estar logado para acessar esta página.")
    st.switch_page("app.py")
    st.stop()

# Proteção de perfil
if st.session_state.get('role') not in ['aprovador', 'administrador']:
    st.error("PÁGINA NÃO AUTORIZADA PARA ESSE USUÁRIO.")
    st.switch_page("pages/01_Painel_de_Controle.py")
    st.stop()

handle_notifications()

st.set_page_config(page_title="Aprovar Pedidos", layout="wide")
st.title("APROVAÇÃO DE PEDIDOS DE COMPRA")

def notify_requester(conn, order_id, new_status):
    """Envia uma notificação para o usuário que criou o pedido."""
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM purchase_orders WHERE id = ?", (order_id,))
    result = cursor.fetchone()
    if result:
        requester_id = result[0]
        message = f"Seu pedido de compra #{order_id} foi {new_status}."
        cursor.execute("INSERT INTO notifications (user_id, message, is_read) VALUES (?, ?, ?)", (requester_id, message, False))
        conn.commit()

def process_approval(order_id, user_id, approved):
    """Processa a aprovação ou reprovação de um pedido."""
    try:
        with sqlite3.connect('database/compras.db') as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM approvals WHERE request_id = ? AND user_id = ?', (order_id, user_id))
            if cursor.fetchone():
                st.warning(f"Você já processou o pedido #{order_id}.")
                return

            cursor.execute('INSERT INTO approvals (request_id, user_id, approved) VALUES (?, ?, ?)', (order_id, user_id, approved))
            
            if approved:
                cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'aprovador'")
                total_approvers = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM approvals WHERE request_id = ? AND approved = ?', (order_id, True))
                approvals_count = cursor.fetchone()[0]
                
                if approvals_count >= total_approvers:
                    cursor.execute("UPDATE purchase_orders SET status = 'aprovado' WHERE id = ?", (order_id,))
                    notify_requester(conn, order_id, "APROVADO e liberado para compra")
                
                st.success(f"Pedido #{order_id} aprovado por você.")
            else:
                cursor.execute("UPDATE purchase_orders SET status = 'reprovado' WHERE id = ?", (order_id,))
                notify_requester(conn, order_id, "REPROVADO")
                st.error(f"Pedido #{order_id} reprovado por você.")
            
            conn.commit()
            st.rerun()

    except Exception as e:
        st.error(f"Erro ao processar aprovação: {e}")

# --- Exibir Pedidos Pendentes ---
try:
    conn = sqlite3.connect('database/compras.db')
    pending_orders = pd.read_sql_query("SELECT * FROM purchase_orders WHERE status = 'pendente'", conn)

    if pending_orders.empty:
        st.info("Nenhum pedido pendente de aprovação no momento.")
    else:
        for index, order in pending_orders.iterrows():
            with st.expander(f"Pedido #{order['id']} - Solicitante: {order['requester']} - Valor: R$ {order['total_value']:,.2f}"):
                st.subheader(f"Detalhes do Pedido #{order['id']}")
                
                items_df = pd.read_sql_query(f"SELECT quantity as Qtde, unit as Unidade, description as Descrição, unit_value as 'Valor Un.', total_value as 'Valor Total' FROM order_items WHERE order_id = {order['id']}", conn)
                st.dataframe(items_df, use_container_width=True)
                
                st.markdown(f"**Justificativa:** {order['justification']}")
                st.markdown(f"**Fornecedor:** {order['supplier_name']} (CNPJ: {order['supplier_cnpj']})")
                st.markdown(f"**Data de Entrega:** {order['delivery_date']}")

                col1, col2 = st.columns(2)
                user_id = st.session_state['user_id']
                with col1:
                    st.button("✅ Aprovar", key=f"approve_{order['id']}", on_click=process_approval, args=(order['id'], user_id, True), use_container_width=True)
                with col2:
                    st.button("❌ Reprovar", key=f"reject_{order['id']}", on_click=process_approval, args=(order['id'], user_id, False), use_container_width=True)

    conn.close()
except Exception as e:
    st.error(f"Erro ao carregar pedidos: {e}")

# Botão de Sair na barra lateral
if st.sidebar.button("Sair"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.switch_page("app.py")
