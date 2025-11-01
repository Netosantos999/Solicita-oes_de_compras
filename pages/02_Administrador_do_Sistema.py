import streamlit as st
import sqlite3
from auth.auth import create_user, hash_password
from auth.utils import handle_notifications
from datetime import datetime
import os

# Proteção da página
if not st.session_state.get('logged_in') or st.session_state.get('role') != 'administrador':
    st.error("PAGINA NÃO AUTORIZADA PARA ESSE USUARIO")
    st.stop()

handle_notifications()

st.set_page_config(page_title="Administração", layout="wide")
st.title("Administrador do Sistema")
st.write(f"Bem-vindo, {st.session_state.get('username')}!")

# Conexão com o banco de dados
# Usamos check_same_thread=False para permitir que o Streamlit gerencie a conexão
conn = sqlite3.connect('database/compras.db', check_same_thread=False)
cursor = conn.cursor()

# Função para buscar todos os usuários
def get_all_users():
    cursor.execute("SELECT id, username, role, email, is_active FROM users")
    return cursor.fetchall()

# --- Exibir todos os usuários ---
st.header("Usuários Cadastrados")
users = get_all_users()
if users:
    user_data = [{"ID": user[0], "Usuário": user[1], "Perfil": user[2], "Email": user[3] or "N/A", "Status": "Ativo" if user[4] == 1 else "Inativo"} for user in users]
    st.dataframe(user_data, use_container_width=True)
else:
    st.info("Nenhum usuário cadastrado.")

# --- Colunas para as funcionalidades ---
col1, col2 = st.columns(2)

# --- Criar novo usuário ---
with col1:
    with st.expander("1. Criar Novo Usuário", expanded=True):
        new_username = st.text_input("Novo Nome de Usuário")
        new_password = st.text_input("Nova Senha", type="password")
        new_role = st.selectbox("Perfil do Usuário", ["Solicitante", "aprovador", "administrador"])
        new_email = st.text_input("Email do Usuário (Obrigatório para notificações)")

        if st.button("Criar Usuário"):
            if new_username and new_password and new_role:
                cursor.execute("SELECT * FROM users WHERE username = ?", (new_username,))
                if cursor.fetchone():
                    st.error("Este nome de usuário já existe.")
                else:
                    # A função create_user precisa ser atualizada para incluir is_active
                    # Por enquanto, fazemos a inserção direta aqui.
                    hashed_pass = hash_password(new_password)
                    cursor.execute(
                        "INSERT INTO users (username, password, role, email, is_active) VALUES (?, ?, ?, ?, 1)",
                        (new_username, hashed_pass, new_role, new_email)
                    )
                    conn.commit()
                    st.success(f"Usuário '{new_username}' criado com sucesso!")
                    st.rerun()
            else:
                st.warning("Por favor, preencha todos os campos.")

# --- Alterar Dados do Usuário ---
with col2:
    with st.expander("2. Alterar Dados do Usuário", expanded=True):
        # Mostra apenas usuários ativos para edição, para evitar confusão
        active_users_list = [user[1] for user in users if user[4] == 1]
        if active_users_list:
            user_to_edit = st.selectbox("Selecione o Usuário para Alterar", active_users_list, key="user_to_edit")
            
            new_user_password = st.text_input("Nova Senha (deixe em branco para não alterar)", type="password", key="new_pass")
            new_user_email = st.text_input("Novo Email (deixe em branco para não alterar)", key="new_email")

            if st.button("Confirmar Alteração"):
                if not new_user_password and not new_user_email:
                    st.warning("Você precisa fornecer uma nova senha ou um novo e-mail.")
                else:
                    updates = []
                    params = []
                    if new_user_password:
                        updates.append("password = ?")
                        params.append(hash_password(new_user_password))
                    if new_user_email:
                        updates.append("email = ?")
                        params.append(new_user_email)
                    
                    query = f"UPDATE users SET {', '.join(updates)} WHERE username = ?"
                    params.append(user_to_edit)
                    
                    cursor.execute(query, tuple(params))
                    conn.commit()
                    st.success(f"Dados do usuário '{user_to_edit}' alterados com sucesso!")
                    st.rerun()
        else:
            st.info("Não há usuários ativos para alterar.")

# --- Gerenciar Status do Usuário (Desativar/Reativar) ---
with st.expander("3. Gerenciar Status do Usuário"):
    users_to_manage = [user[1] for user in users if user[1] != st.session_state.get('username')]
    if users_to_manage:
        user_to_manage_status = st.selectbox("Selecione o Usuário", users_to_manage, key="user_status")
        
        # Descobre o status atual do usuário selecionado
        current_status = None
        for user in users:
            if user[1] == user_to_manage_status:
                current_status = user[4]
                break
        
        action_text = "Desativar" if current_status == 1 else "Reativar"
        
        if st.button(f"{action_text} Usuário '{user_to_manage_status}'", type="primary"):
            new_status = 0 if current_status == 1 else 1
            cursor.execute("UPDATE users SET is_active = ? WHERE username = ?", (new_status, user_to_manage_status))
            conn.commit()
            st.success(f"Usuário '{user_to_manage_status}' foi {'desativado' if new_status == 0 else 'reativado'}!")
            st.rerun()
    else:
        st.info("Não há outros usuários para gerenciar.")

# --- Backup do Banco de Dados ---
st.divider()
st.header("Manutenção do Sistema")
with st.expander("Backup do Banco de Dados"):
    st.info("Clique no botão abaixo para fazer o download de uma cópia de segurança completa do banco de dados.")
    
    db_path = 'database/compras.db'
    if os.path.exists(db_path):
        with open(db_path, "rb") as fp:
            # Gera um nome de arquivo com data e hora
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"backup_compras_{timestamp}.db"
            
            st.download_button(
                label="Gerar Backup do Banco de Dados",
                data=fp,
                file_name=file_name,
                mime="application/octet-stream"
            )
    else:
        st.error("Arquivo do banco de dados não encontrado.")


# Botão de Sair na barra lateral
if st.sidebar.button("Sair"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.switch_page("app.py")
