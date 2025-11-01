import streamlit as st
import sqlite3
from auth.auth import create_user, hash_password
from auth.utils import handle_notifications

# Proteção da página
if not st.session_state.get('logged_in') or st.session_state.get('role') != 'administrador':
    st.error("PAGINA NÃO AUTORIZADA PARA ESSE USUARIO")
    st.stop()

handle_notifications()

st.set_page_config(page_title="Administração", layout="wide")
st.title("Administrador do Sistema")
st.write(f"Bem-vindo, {st.session_state.get('username')}!")

# Conexão com o banco de dados
conn = sqlite3.connect('database/compras.db')
cursor = conn.cursor()

# Função para buscar todos os usuários
def get_all_users():
    cursor.execute("SELECT id, username, role, email FROM users")
    return cursor.fetchall()

# --- Exibir todos os usuários ---
st.header("Usuários Cadastrados")
users = get_all_users()
if users:
    # Exibe os usuários em um formato mais limpo
    user_data = [{"ID": user[0], "Usuário": user[1], "Perfil": user[2], "Email": user[3] or "N/A"} for user in users]
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
                # Verifica se o usuário já existe
                cursor.execute("SELECT * FROM users WHERE username = ?", (new_username,))
                if cursor.fetchone():
                    st.error("Este nome de usuário já existe.")
                else:
                    create_user(new_username, new_password, new_role, new_email)
                    st.success(f"Usuário '{new_username}' criado com sucesso!")
                    st.rerun() # Recarrega a página para mostrar o novo usuário
            else:
                st.warning("Por favor, preencha todos os campos.")

# --- Alterar Dados do Usuário (Senha e/ou Email) ---
with col2:
    with st.expander("2. Alterar Dados do Usuário", expanded=True):
        users_list = [user[1] for user in users]
        user_to_edit = st.selectbox("Selecione o Usuário para Alterar", users_list, key="user_to_edit")
        
        new_user_password = st.text_input("Nova Senha (deixe em branco para não alterar)", type="password", key="new_pass")
        new_user_email = st.text_input("Novo Email (deixe em branco para não alterar)", key="new_email")

        if st.button("Confirmar Alteração"):
            if not new_user_password and not new_user_email:
                st.warning("Você precisa fornecer uma nova senha ou um novo e-mail.")
            else:
                try:
                    # Lógica para construir a query dinamicamente
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
                except Exception as e:
                    st.error(f"Ocorreu um erro ao alterar os dados: {e}")


# --- Excluir usuário ---
with st.expander("3. Excluir Usuário"):
    users_to_delete = [user[1] for user in users if user[1] != st.session_state.get('username')]
    if users_to_delete:
        user_to_delete = st.selectbox("Selecione o Usuário para Excluir", users_to_delete)
        st.warning(f"Atenção: Esta ação é irreversível. Todos os dados associados ao usuário '{user_to_delete}' serão removidos.")
        
        if st.button("Excluir Usuário Permanentemente", type="primary"):
            try:
                # Não permitir que o admin logado se exclua
                if user_to_delete == st.session_state.get('username'):
                    st.error("Você não pode excluir a si mesmo.")
                else:
                    cursor.execute("DELETE FROM users WHERE username = ?", (user_to_delete,))
                    conn.commit()
                    st.success(f"Usuário '{user_to_delete}' excluído com sucesso!")
                    st.rerun() # Recarrega a página para atualizar a lista
            except Exception as e:
                st.error(f"Ocorreu um erro ao excluir o usuário: {e}")
    else:
        st.info("Não há outros usuários para excluir.")


# Fechar a conexão com o banco de dados no final
conn.close()

# Botão de Sair na barra lateral
if st.sidebar.button("Sair"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.switch_page("app.py")
