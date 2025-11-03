import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from auth.utils import handle_notifications
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Proteção de acesso à página
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.error("Você precisa estar logado para acessar esta página.")
    st.switch_page("app.py")
    st.stop()

# --- FUNÇÃO DE ENVIO DE E-MAIL ---
def send_email_notification(order_details, items_df, recipient_emails):
    """Envia um e-mail de notificação detalhado e retorna True em sucesso, False em falha."""
    if not recipient_emails:
        st.warning("AVISO: Pedido salvo, mas não há e-mails de aprovadores/administradores cadastrados para enviar a notificação.")
        return True

    try:
        # As credenciais de e-mail devem ser configuradas no st.secrets
        creds = st.secrets["email_credentials"]
        sender_email = creds["sender_email"]
        password = creds["sender_password"]
        smtp_server = creds["smtp_server"]
        smtp_port = creds["smtp_port"]

        message = MIMEMultipart("alternative")
        message["Subject"] = f"Novo Pedido de Compra para Aprovação - Nº {order_details['po_number']}"
        message["From"] = sender_email
        message["To"] = ", ".join(recipient_emails)

        # Formata o DataFrame de itens para uma tabela HTML bonita
        items_html = items_df.to_html(index=False, justify='center', border=0).replace(
            '<table', '<table style="width:100%; border-collapse: collapse; font-family: Arial, sans-serif;"'
        ).replace(
            '<thead>', '<thead style="background-color: #f2f2f2;">'
        ).replace(
            '<th>', '<th style="padding: 12px; text-align: left; border-bottom: 1px solid #ddd;">'
        ).replace(
            '<td>', '<td style="padding: 12px; text-align: left; border-bottom: 1px solid #ddd;">'
        )

        # Template HTML do e-mail
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; line-height: 1.6; }}
                .container {{ max-width: 800px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px; background-color: #fdfdfd; }}
                h2 {{ color: #0056b3; border-bottom: 2px solid #0056b3; padding-bottom: 10px; }}
                h3 {{ color: #444; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 30px; }}
                ul {{ list-style-type: none; padding: 0; }}
                li {{ margin-bottom: 12px; background-color: #f9f9f9; padding: 15px; border-left: 5px solid #0056b3; border-radius: 5px; }}
                strong {{ color: #333; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Novo Pedido de Compra para Aprovação</h2>
                <p>Um novo pedido de compra foi enviado e requer sua atenção.</p>
                
                <h3>Detalhes Gerais</h3>
                <ul>
                    <li><strong>Pedido Nº:</strong> {order_details['po_number']}</li>
                    <li><strong>Solicitante:</strong> {order_details['requester']}</li>
                    <li><strong>Data do Pedido:</strong> {datetime.now().strftime('%d/%m/%Y')}</li>
                    <li><strong>Valor Total:</strong> R$ {order_details['total_value']:,.2f}</li>
                    <li><strong>Justificativa:</strong> {order_details['justification'] or 'Não informada'}</li>
                </ul>

                <h3>Itens do Pedido</h3>
                {items_html}

                <h3>Dados do Fornecedor</h3>
                <ul>
                    <li><strong>Razão Social:</strong> {order_details['supplier_name'] or 'Não informado'}</li>
                    <li><strong>CNPJ:</strong> {order_details['supplier_cnpj'] or 'Não informado'}</li>
                    <li><strong>Contato:</strong> {order_details['supplier_contact'] or 'Não informado'}</li>
                    <li><strong>Forma de Pagamento:</strong> {order_details['payment_method'] or 'Não informada'}</li>
                    <li><strong>Dados Bancários / PIX:</strong> {order_details['bank_details'] or 'Não informado'}</li>
                </ul>

                <h3>Informações de Entrega</h3>
                <ul>
                    <li><strong>Data de Entrega Prevista:</strong> {order_details['delivery_date']}</li>
                    <li><strong>Endereço de Entrega:</strong> {order_details['delivery_address'].replace('\n', '<br>')}</li>
                </ul>

                <p style="margin-top: 30px; text-align: center; font-size: 1.1em;">
                    Por favor, acesse o <strong>Sistema de Compras</strong> para revisar e aprovar o pedido.
                </p>
            </div>
        </body>
        </html>
        """
        message.attach(MIMEText(html, "html"))
        
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient_emails, message.as_string())
        
        st.info("Notificação por e-mail enviada com sucesso para os aprovadores.")
        return True
    except KeyError as e:
        st.error(f"FALHA NO ENVIO DE E-MAIL: Credenciais de e-mail não configuradas em 'st.secrets'. Verifique a chave: {e}")
        return False
    except Exception as e:
        st.error(f"FALHA NO ENVIO DE E-MAIL: O pedido foi salvo, mas a notificação falhou. Causa: {e}")
        return False

# --- LÓGICA DE CONTROLE DE ESTADO DO FORMULÁRIO ---
def create_new_order():
    """Limpa o estado para permitir um novo pedido."""
    keys_to_delete = ['form_submitted', 'last_order_id', 'items_df']
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]




handle_notifications()
st.set_page_config(page_title="Novo Pedido de Compra", layout="wide")

# --- LÓGICA DE EXIBIÇÃO (FORMULÁRIO OU SUCESSO) ---
if st.session_state.get('form_submitted', False):
    st.success(f"Pedido de Compra #{st.session_state.get('last_order_id', '')} enviado para aprovação com sucesso!")
    st.balloons()
    st.info("Você pode criar um novo pedido ou navegar para outra página.")
    st.button("Criar Novo Pedido", on_click=create_new_order)
else:
    # --- EXIBE O FORMULÁRIO ---
    st.title("FORMULÁRIO DE PEDIDO DE COMPRA")

    def get_next_po_number():
        try:
            with sqlite3.connect('database/compras.db') as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(id) FROM purchase_orders")
                last_id = cursor.fetchone()[0]
                return (last_id or 0) + 1
        except Exception:
            return 1

    col1, col2, col3 = st.columns(3)
    with col1:
        st.text_input("Data", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)
    with col2:
        requester = st.text_input("Solicitante", value=st.session_state.get('username', ''), disabled=True)
    with col3:
        po_number = st.text_input("Nº Pedido", value=str(get_next_po_number()), disabled=True)

    st.header("DESCRIÇÃO DO PEDIDO")
    if 'items_df' not in st.session_state:
        st.session_state.items_df = pd.DataFrame([{"Qtde": 1, "Unidade": "UNI", "Descrição": "", "Valor Un.": 0.00}])

    edited_df = st.data_editor(
        st.session_state.items_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Qtde": st.column_config.NumberColumn("Qtde", required=True, min_value=1),
            "Unidade": st.column_config.TextColumn("Unidade", required=True),
            "Descrição": st.column_config.TextColumn("Descrição", required=True, width="large"),
            "Valor Un.": st.column_config.NumberColumn("Valor Un.", format="R$ %.2f", required=True, min_value=0.0),
        }
    )
    edited_df['Valor Total'] = edited_df['Qtde'] * edited_df['Valor Un.']
    total_geral = edited_df['Valor Total'].sum()
    st.metric("TOTAL GERAL DO PEDIDO", f"R$ {total_geral:,.2f}")

    st.header("INFORMAÇÕES ADICIONAIS")
    justification = st.text_area("JUSTIFICATIVA PEDIDO DE COMPRA")
    spreadsheet_link = st.text_input("LINK PLANILHA ONLINE")

    with st.expander("DADOS DO FORNECEDOR"):
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            supplier_name = st.text_input("Razão Social")
            payment_method = st.selectbox("Forma de Pagamento", ["PIX", "Boleto", "Transferência Bancária", "Cartão de Crédito"])
            bank_details = st.text_area("Banco/Agência/Conta ou Chave PIX")
        with f_col2:
            supplier_cnpj = st.text_input("CNPJ")
            supplier_contact = st.text_input("Contato")

    with st.expander("DADOS ENTREGA / FATURAMENTO"):
        e_col1, e_col2 = st.columns(2)
        with e_col1:
            delivery_date = st.date_input("Data de Entrega")
        with e_col2:
            due_date = st.date_input("Vencimento")
        delivery_address = st.text_area("Endereço de Entrega", "T ENGENHARIA E SISTEMAS\nCNPJ: 05.278.989/0003-85")

    if st.button("Enviar Pedido para Aprovação", type="primary"):
        if edited_df.empty or edited_df['Descrição'].iloc[0] == '':
            st.error("Adicione pelo menos um item ao pedido.")
        else:
            email_sent_successfully = False
            try:
                with sqlite3.connect('database/compras.db') as conn:
                    cursor = conn.cursor()
                    
                    # Coleta todos os detalhes do pedido em um dicionário para facilitar o uso
                    order_details_dict = {
                        'user_id': st.session_state['user_id'],
                        'requester': st.session_state.get('username', ''),
                        'po_number': po_number,
                        'justification': justification,
                        'spreadsheet_link': spreadsheet_link,
                        'supplier_name': supplier_name,
                        'supplier_cnpj': supplier_cnpj,
                        'supplier_contact': supplier_contact,
                        'payment_method': payment_method,
                        'bank_details': bank_details,
                        'delivery_date': str(delivery_date),
                        'due_date': str(due_date),
                        'delivery_address': delivery_address,
                        'total_value': total_geral,
                        'status': 'pendente'
                    }

                    # Insere o pedido principal usando o dicionário
                    cursor.execute("""
                        INSERT INTO purchase_orders (user_id, requester, po_number, justification, spreadsheet_link, supplier_name, supplier_cnpj, supplier_contact, payment_method, bank_details, delivery_date, due_date, delivery_address, total_value, status)
                        VALUES (:user_id, :requester, :po_number, :justification, :spreadsheet_link, :supplier_name, :supplier_cnpj, :supplier_contact, :payment_method, :bank_details, :delivery_date, :due_date, :delivery_address, :total_value, :status)
                    """, order_details_dict)
                    
                    order_id = cursor.lastrowid
                    st.session_state.last_order_id = order_id

                    # CORREÇÃO: Inserindo os itens um a um para evitar o erro.
                    for index, row in edited_df.iterrows():
                        cursor.execute("INSERT INTO order_items (order_id, quantity, unit, description, unit_value, total_value) VALUES (?, ?, ?, ?, ?, ?)",
                                       (order_id, row['Qtde'], row['Unidade'], row['Descrição'], row['Valor Un.'], row['Valor Total']))
                    
                    # Cria notificações no sistema
                    cursor.execute("SELECT id FROM users WHERE role = 'aprovador' AND is_active = 1")
                    approvers = cursor.fetchall()
                    for approver in approvers:
                        message_popup = f"Novo pedido de compra #{order_id} (Total: R$ {total_geral:,.2f}) aguardando sua aprovação."
                        cursor.execute("INSERT INTO notifications (user_id, message, is_read) VALUES (?, ?, ?)", (approver[0], message_popup, False))
                    
                    # Busca e-mails para notificação
                    cursor.execute("SELECT email FROM users WHERE (role = 'aprovador' OR role = 'administrador') AND email IS NOT NULL AND email != '' AND is_active = 1")
                    recipient_emails = [row[0] for row in cursor.fetchall()]
                    
                    conn.commit()
                    st.success(f"Pedido #{order_id} salvo com sucesso no sistema!")

                    # Envia o e-mail detalhado
                    email_sent_successfully = send_email_notification(order_details_dict, edited_df, recipient_emails)

            except sqlite3.Error as e:
                st.error(f"Ocorreu um erro no banco de dados ao salvar o pedido: {e}")
            except Exception as e:
                st.error(f"Ocorreu um erro CRÍTICO ao salvar o pedido: {e}")

            if email_sent_successfully:
                st.session_state.form_submitted = True
                st.rerun()

# Botão de Sair na barra lateral
if st.sidebar.button("Sair"):
    create_new_order()
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.switch_page("app.py")
