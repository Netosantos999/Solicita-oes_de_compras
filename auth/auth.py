import streamlit as st
import sqlite3
import hashlib

def hash_password(password):
    """Cria um hash SHA256 para a senha fornecida."""
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_password(hashed_password, user_password):
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    return hashed_password == hash_password(user_password)

def create_user(username, password, role, email): # Adicionado 'email'
    """Cria um novo usuário no banco de dados com e-mail."""
    conn = sqlite3.connect('database/compras.db')
    cursor = conn.cursor()
    # Adicionado 'email' ao INSERT
    cursor.execute('INSERT INTO users (username, password, role, email) VALUES (?, ?, ?, ?)', 
                   (username, hash_password(password), role, email))
    conn.commit()
    conn.close()

def login_user(username, password):
    """Autentica um usuário e armazena seus dados na sessão."""
    conn = sqlite3.connect('database/compras.db')
    cursor = conn.cursor()
    
    # CORREÇÃO: Busca o id, password e role do usuário
    cursor.execute('SELECT id, password, role FROM users WHERE username = ?', (username,))
    data = cursor.fetchone()
    conn.close()
    
    if data:
        # CORREÇÃO: Desempacota os três valores (id, hash, role)
        user_id, hashed_password, role = data
        
        if check_password(hashed_password, password):
            # Se a senha estiver correta, armazena todos os dados na sessão
            st.session_state['logged_in'] = True
            st.session_state['user_id'] = user_id  # <-- A LINHA QUE FALTAVA
            st.session_state['username'] = username
            st.session_state['role'] = role
            return True
            
    # Se o usuário não for encontrado ou a senha estiver errada
    return False
