import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from auth.utils import handle_notifications
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- FUNÇÃO DE ENVIO DE E-MAIL ---
def send_email_notification(order_id, requester_name, total_value, recipient_emails):
    """Envia um e-mail de notificação para a lista de destinatários."""
    if not recipient_emails:
        st.warning("Nenhum e-mail de destinatário encontrado para enviar a notificação.")
        return False

    try:
        creds = st.secrets["email_credentials"]
        sender_email = creds["sender_email"]
        password = creds["sender_password"]
        smtp_server = creds["smtp_server"]
        smtp_port = creds["smtp_port"]

        message = MIMEMultipart("alternative")
        message["Subject"] = f"Novo Pedido de Compra para Aprovação Da Obra MDA"
        message["From"] = sender_email
        message["To"] = ", ".join(recipient_emails)

        html = f"""
        <html><body>
            <h2>Novo Pedido de Compra para Aprovação</h2>
            <p>Um novo pedido de compra foi enviado e requer sua atenção.</p>
            <ul>
                <li><strong>Pedido Nº:</strong> {order_id}</li>
                <li><strong>Solicitante:</strong> {requester_name}</li>
                <li><strong>Valor Total:</strong> R$ {total_value:,.2f}</li>
            </ul>
            <p>Por favor, acesse o sistema para revisar e aprovar o pedido.</p>
        </body></html>
        """
        message.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient_emails, message.as_string())
        
        return True
    except Exception as e:
        st.warning(f"AVISO: O pedido foi salvo, mas a notificação por e-mail falhou. Causa: {e}")
        return False

# Proteção da página
if not st.session_state.get('logged_in') or st.session_state.get('role') not in ['Solicitante', 'administrador', 'aprovador']:
    st.error("PAGINA NÃO AUTORIZADA PARA ESSE USUARIO")
    st.stop()

handle_notifications()

st.set_page_config(page_title="Novo Pedido de Compra", layout="wide")
st.title("FORMULÁRIO DE PEDIDO DE COMPRA")

def get_next_po_number():
    """Busca o último ID de pedido e retorna o próximo número sequencial."""
    try:
        conn = sqlite3.connect('database/compras.db')
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM purchase_orders")
        last_id = cursor.fetchone()[0]
        conn.close()
        if last_id is None:
            return 1
        else:
            return last_id + 1
    except Exception:
        return 1

# --- Dados Iniciais ---
col1, col2, col3 = st.columns(3)
with col1:
    st.text_input("Data", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)
with col2:
    requester = st.text_input("Solicitante", value=st.session_state.get('username', ''), disabled=True)
with col3:
    next_po_number = get_next_po_number()
    po_number = st.text_input("Nº Pedido", value=str(next_po_number), disabled=True)

# --- Itens do Pedido (Editor de Dados) ---
st.header("DESCRIÇÃO DO PEDIDO")

items_df = pd.DataFrame([
    {"Qtde": 1, "Unidade": "UNI", "Descrição": "", "Valor Un.": 0.00}
])

edited_df = st.data_editor(
    items_df,
    num_rows="dynamic",
    # CORREÇÃO: use_container_width trocado por width
    use_container_width=True,
    column_config={
        "Qtde": st.column_config.NumberColumn("Qtde", required=True, min_value=0),
        "Unidade": st.column_config.TextColumn("Unidade", required=True),
        "Descrição": st.column_config.TextColumn("Descrição", required=True, width="large"),
        "Valor Un.": st.column_config.NumberColumn("Valor Un.", format="R$ %.2f", required=True),
    }
)

edited_df['Valor Total'] = edited_df['Qtde'] * edited_df['Valor Un.']
total_geral = edited_df['Valor Total'].sum()
st.metric("TOTAL GERAL DO PEDIDO", f"R$ {total_geral:,.2f}")

# --- Informações Adicionais ---
st.header("INFORMAÇÕES ADICIONAIS")
justification = st.text_area("JUSTIFICATIVA PEDIDO DE COMPRA")
spreadsheet_link = st.text_input("LINK PLANILHA ONLINE")

# --- Dados do Fornecedor ---
with st.expander("DADOS DO FORNECEDOR"):
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        supplier_name = st.text_input("Razão Social")
        payment_method = st.selectbox("Forma de Pagamento", ["PIX", "Boleto", "Transferência Bancária", "Cartão de Crédito"])
        bank_details = st.text_area("Banco/Agência/Conta ou Chave PIX")
    with f_col2:
        supplier_cnpj = st.text_input("CNPJ")
        supplier_contact = st.text_input("Contato")

# --- Dados de Entrega ---
with st.expander("DADOS ENTREGA / FATURAMENTO"):
    e_col1, e_col2 = st.columns(2)
    with e_col1:
        delivery_date = st.date_input("Data de Entrega")
    with e_col2:
        due_date = st.date_input("Vencimento")
    delivery_address = st.text_area("Endereço de Entrega", "T ENGENHARIA E SISTEMAS\nCNPJ: 05.278.989/0003-85")


# --- Botão de Envio ---
if st.button("Enviar Pedido para Aprovação", type="primary"):
    if edited_df.empty or edited_df['Descrição'].iloc[0] == '':
        st.error("Adicione pelo menos um item ao pedido.")
    else:
        order_id = None
        conn = None
        try:
            conn = sqlite3.connect('database/compras.db')
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO purchase_orders (user_id, requester, po_number, justification, spreadsheet_link, supplier_name, supplier_cnpj, supplier_contact, payment_method, bank_details, delivery_date, due_date, delivery_address, total_value, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                st.session_state['user_id'], st.session_state.get('username', ''), po_number, justification, spreadsheet_link, supplier_name, supplier_cnpj, supplier_contact, payment_method, bank_details, str(delivery_date), str(due_date), delivery_address, total_geral, 'pendente'
            ))
            order_id = cursor.lastrowid

            for index, row in edited_df.iterrows():
                cursor.execute("""
                    INSERT INTO order_items (order_id, quantity, unit, description, unit_value, total_value)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (order_id, row['Qtde'], row['Unidade'], row['Descrição'], row['Valor Un.'], row['Valor Total']))

            conn.commit()
            st.success(f"Pedido de Compra #{order_id} salvo com sucesso no sistema!")
            st.balloons()

        except Exception as e:
            st.error(f"Ocorreu um erro CRÍTICO ao salvar o pedido no banco de dados: {e}")
            if conn:
                conn.rollback()
            st.stop()
        finally:
            if conn:
                conn.close()

        if order_id:
            try:
                conn = sqlite3.connect('database/compras.db')
                cursor = conn.cursor()

                cursor.execute("SELECT id FROM users WHERE role = 'aprovador'")
                approvers = cursor.fetchall()
                for approver in approvers:
                    message_popup = f"Novo pedido de compra #{order_id} (Total: R$ {total_geral:,.2f}) aguardando sua aprovação."
                    cursor.execute("INSERT INTO notifications (user_id, message, is_read) VALUES (?, ?, ?)", (approver[0], message_popup, False))
                
                conn.commit()

                cursor.execute("SELECT email FROM users WHERE (role = 'aprovador' OR role = 'administrador') AND email IS NOT NULL AND email != ''")
                recipient_emails = [row[0] for row in cursor.fetchall()]
                
                if recipient_emails:
                    if send_email_notification(order_id, st.session_state.get('username', ''), total_geral, recipient_emails):
                        st.info("Notificação por e-mail enviada com sucesso.")
                else:
                    st.warning("AVISO: Pedido salvo, mas não há e-mails de aprovadores/administradores cadastrados para enviar a notificação.")

            except Exception as e:
                st.warning(f"AVISO: O pedido foi salvo, mas ocorreu um erro ao criar as notificações: {e}")
            finally:
                if conn:
                    conn.close()

# Botão de Sair na barra lateral
if st.sidebar.button("Sair"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.switch_page("app.py")
