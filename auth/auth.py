import sqlite3
import hashlib
import streamlit as st

def hash_password(password):
    """Gera o hash de uma senha usando SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(hashed_password, user_password):
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    return hashed_password == hash_password(user_password)

def create_user(username, password, role, email):
    """Cria um novo usuário no banco de dados."""
    hashed_pass = hash_password(password)
    try:
        with sqlite3.connect('database/compras.db') as conn:
            cursor = conn.cursor()
            # Garante que novos usuários sejam criados como ativos (is_active = 1)
            cursor.execute(
                "INSERT INTO users (username, password, role, email, is_active) VALUES (?, ?, ?, ?, 1)",
                (username, hashed_pass, role, email)
            )
            conn.commit()
    except sqlite3.IntegrityError:
        st.error("Erro: Nome de usuário já existe.")

def login_user(username, password):
    """Autentica um usuário e retorna o status e uma mensagem."""
    with sqlite3.connect('database/compras.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, password, role, is_active FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()

    if user_data:
        user_id, hashed_password, role, is_active = user_data
        
        if check_password(hashed_password, password):
            if is_active == 1:
                # Login bem-sucedido: atualiza o estado da sessão
                st.session_state['logged_in'] = True
                st.session_state['user_id'] = user_id
                st.session_state['username'] = username
                st.session_state['role'] = role
                return True, "Login bem-sucedido!"
            else:
                # Usuário desativado
                return False, "Este usuário foi desativado. Contate o administrador."
        else:
            # Senha incorreta
            return False, "Usuário ou senha incorretos."
    else:
        # Usuário não encontrado
        return False, "Usuário ou senha incorretos."
