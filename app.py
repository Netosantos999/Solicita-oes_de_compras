import streamlit as st
from auth.auth import login_user
from database.db import create_tables, seed_main_admin

# Configuração da página deve ser o primeiro comando
st.set_page_config(
    page_title="Sistema de Compras - Login",
    layout="centered"
)

# Garante que o banco de dados e o admin existam
create_tables()
seed_main_admin()

# --- Lógica de Login ---

# Inicializa o estado de login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# Se o usuário já estiver logado, mostra uma mensagem e impede a execução do código de login
if st.session_state['logged_in']:
    st.switch_page("pages/01_Painel_de_Controle.py")

# --- Formulário de Login ---
st.title("Sistema de Solicitação de Compras")
st.header("Login")

username = st.text_input("Usuário")
password = st.text_input("Senha", type="password")

if st.button("Entrar"):
    if login_user(username, password):
        # Se o login for bem-sucedido, define o estado e redireciona
        st.session_state['logged_in'] = True
        st.switch_page("pages/01_Painel_de_Controle.py")
    else:
        st.error("Usuário ou senha incorretos.")
