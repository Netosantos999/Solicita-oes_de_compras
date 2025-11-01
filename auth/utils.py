import streamlit as st
import sqlite3
import hashlib

def hash_password(password):
    """Cria um hash SHA256 para a senha fornecida."""
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_password(hashed_password, user_password):
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    return hashed_password == hash_password(user_password)

def create_user(username, password, role):
    """Cria um novo usuário no banco de dados."""
    conn = sqlite3.connect('database/compras.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, hash_password(password), role))
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

def handle_notifications():
    """
    Verifica se há notificações não lidas e as exibe em um 
    pop-up (st.dialog) que exige interação do usuário para fechar.
    """
    # Só executa se o usuário estiver logado
    if not st.session_state.get('logged_in'):
        return

    user_id = st.session_state.get('user_id')
    if not user_id:
        return

    try:
        conn = sqlite3.connect('database/compras.db')
        cursor = conn.cursor()

        # Busca todas as notificações não lidas
        cursor.execute("SELECT id, message FROM notifications WHERE user_id = ? AND is_read = ?", (user_id, False))
        unread_notifications = cursor.fetchall()

        if unread_notifications:
            # Define o conteúdo do pop-up
            @st.dialog("Você tem novas notificações!", dismissible=False)
            def show_notification_dialog():
                for _, message in unread_notifications:
                    st.info(message, icon="🔔")
                
                if st.button("Fechar", use_container_width=True):
                    # Marca todas as notificações exibidas como lidas
                    with sqlite3.connect('database/compras.db') as conn_inner:
                        cursor_inner = conn_inner.cursor()
                        for notif_id, _ in unread_notifications:
                            cursor_inner.execute("UPDATE notifications SET is_read = ? WHERE id = ?", (True, notif_id))
                        conn_inner.commit()
                    st.rerun()

            # Chama o pop-up
            show_notification_dialog()
            
    except sqlite3.Error:
        # Ignora erros de banco de dados silenciosamente
        pass
    finally:
        if 'conn' in locals() and conn:
            conn.close()
