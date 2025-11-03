import streamlit as st
import sqlite3
from auth.utils import handle_notifications

# Proteção de acesso à página
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.error("Você precisa estar logado para acessar esta página.")
    st.switch_page("app.py")
    st.stop()

handle_notifications()

st.set_page_config(page_title="Minhas Notificações", layout="centered")
st.title("Histórico de Notificações")

try:
    conn = sqlite3.connect('database/compras.db')
    cursor = conn.cursor()
    
    user_id = st.session_state.get('user_id')
    
    # Mostra todas as notificações, lidas ou não, como um histórico
    cursor.execute("SELECT message, is_read FROM notifications WHERE user_id = ? ORDER BY id DESC", (user_id,))
    notifications = cursor.fetchall()
    
    if not notifications:
        st.info("Você não tem nenhuma notificação no seu histórico.")
    else:
        for message, is_read in notifications:
            if is_read:
                st.success(message, icon="✅") # Notificações já vistas
            else:
                st.warning(message, icon="🔔") # Notificações novas

    conn.close()
except Exception as e:
    st.error(f"Erro ao carregar histórico de notificações: {e}")

# Botão de Sair na barra lateral
if st.sidebar.button("Sair"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.switch_page("app.py")
