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
    conn = sqlite3.connect('database/compras.db')
    cursor = conn.cursor()
    hashed_pass = hash_password(password)
    try:
        # Garante que novos usuários sejam criados como ativos (is_active = 1)
        cursor.execute(
            "INSERT INTO users (username, password, role, email, is_active) VALUES (?, ?, ?, ?, 1)",
            (username, hashed_pass, role, email)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # Este erro ocorre se o nome de usuário já existir (devido à restrição UNIQUE)
        st.error("Erro: Nome de usuário já existe.")
    finally:
        conn.close()

def login_user(username, password):
    """Autentica um usuário e gerencia o estado da sessão."""
    conn = sqlite3.connect('database/compras.db')
    cursor = conn.cursor()
    
    # Seleciona também a coluna 'is_active'
    cursor.execute("SELECT id, password, role, is_active FROM users WHERE username = ?", (username,))
    user_data = cursor.fetchone()
    conn.close()

    if user_data:
        user_id, hashed_password, role, is_active = user_data
        
        # 1. Verifica a senha
        if check_password(hashed_password, password):
            # 2. Verifica se o usuário está ativo
            if is_active == 1:
                # Login bem-sucedido
                st.session_state['logged_in'] = True
                st.session_state['user_id'] = user_id
                st.session_state['username'] = username
                st.session_state['role'] = role
                return True, "Login bem-sucedido!"
            else:
                # Usuário correto, senha correta, mas desativado
                return False, "Este usuário foi desativado. Contate o administrador."
        else:
            # Senha incorreta
            return False, "Nome de usuário ou senha incorretos."
    else:
        # Usuário não encontrado
        return False, "Nome de usuário ou senha incorretos."
