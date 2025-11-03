import sqlite3
import hashlib
import os

# Função para hashear a senha
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_tables():
    """Cria todas as tabelas necessárias se elas não existirem."""
    os.makedirs('database', exist_ok=True)
    with sqlite3.connect('database/compras.db') as conn:
        cursor = conn.cursor()

        # Tabela de usuários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                email TEXT,
                is_active INTEGER NOT NULL DEFAULT 1 
            )
        """)

        # Tabela de pedidos de compra
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchase_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                requester TEXT NOT NULL,
                po_number TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pendente',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_value REAL,
                justification TEXT,
                spreadsheet_link TEXT,
                supplier_name TEXT,
                supplier_cnpj TEXT,
                supplier_contact TEXT,
                payment_method TEXT,
                bank_details TEXT,
                delivery_date TEXT,
                due_date TEXT,
                delivery_address TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        # Tabela de itens do pedido
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                quantity INTEGER NOT NULL,
                unit TEXT NOT NULL,
                description TEXT NOT NULL,
                unit_value REAL NOT NULL,
                total_value REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES purchase_orders (id)
            )
        """)

        # Tabela de aprovações
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                user_id INTEGER,
                status TEXT NOT NULL, 
                comments TEXT,
                approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES purchase_orders (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        # Tabela de notificações
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0, 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        conn.commit()

def seed_main_admin():
    """Garante que o administrador principal exista no banco de dados."""
    with sqlite3.connect('database/compras.db') as conn:
        cursor = conn.cursor()

        admin_username = "Francelino Neto Santos"
        admin_password = "02475882379"
        admin_email = "francelino.santos@tees.com.br"
        hashed_password = hash_password(admin_password)

        cursor.execute("""
            INSERT OR REPLACE INTO users (username, password, role, email, is_active)
            VALUES (?, ?, 'administrador', ?, 1)
        """, (admin_username, hashed_password, admin_email))
        
        conn.commit()

if __name__ == '__main__':
    print("Inicializando o banco de dados...")
    create_tables()
    seed_main_admin()
    print("Banco de dados e administrador principal prontos.")
