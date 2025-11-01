Sistema de Solicitação de Compras
Este é um sistema web completo para gerenciamento de pedidos de compra, desenvolvido com Python e Streamlit. Ele permite um fluxo de trabalho estruturado com diferentes níveis de permissão para criação, aprovação e administração de pedidos e usuários.

Tecnologias Utilizadas
Linguagem: Python 3
Framework Web: Streamlit
Banco de Dados: SQLite3
Bibliotecas Principais: Pandas, Plotly Express
Perfis de Usuário e Funcionalidades
O sistema opera com base em três perfis de usuário distintos, cada um com acesso a funcionalidades específicas para garantir a segurança e a organização do processo de compras.

1. Perfil: Solicitante
O Solicitante é o usuário base do sistema, responsável por iniciar o processo de compra.

Funcionalidades:
Login: Acessa o sistema com seu nome de usuário e senha.
Painel de Controle: Visualiza um painel personalizado contendo apenas os seus próprios pedidos, com um gráfico de status (pendente, aprovado, rejeitado) e uma lista detalhada.
Novo Pedido de Compra: Acessa um formulário completo para criar um novo pedido, incluindo:
Múltiplos itens com quantidade, descrição e valor.
Justificativa da compra.
Dados do fornecedor e de faturamento.
Notificações: Recebe notificações no sistema (ícone de sino e pop-up) quando um de seus pedidos é aprovado ou rejeitado.
Sair (Logout): Encerra a sessão de forma segura.
2. Perfil: Aprovador
O Aprovador tem todas as permissões do Solicitante e, adicionalmente, a responsabilidade de analisar e validar os pedidos.

Funcionalidades (além das de Solicitante):
Painel de Controle Global: Visualiza todos os pedidos de todos os usuários do sistema, permitindo uma visão geral completa.
Aprovar Pedidos: Acessa uma página dedicada onde pode:
Ver a lista de todos os pedidos com status "pendente".
Expandir cada pedido para ver os detalhes completos (itens, valores, justificativa).
Aprovar ou Rejeitar um pedido com um único clique.
Notificações de Novos Pedidos: Recebe notificações por e-mail e no sistema (pop-up) sempre que um novo pedido é submetido para aprovação.
3. Perfil: Administrador
O Administrador é o superusuário do sistema. Ele possui todas as permissões de um Aprovador e, adicionalmente, tem controle total sobre os usuários e a manutenção do sistema.

Funcionalidades (além das de Aprovador):
Acesso Total: Pode criar, aprovar e visualizar todos os aspectos do sistema.
Página de Administração: Acessa uma área exclusiva para gerenciamento completo:
Criar Usuários: Cadastra novos usuários, definindo seu nome, senha, e-mail e perfil (Solicitante, Aprovador ou Administrador).
Alterar Dados de Usuários: Modifica a senha e/ou o e-mail de qualquer usuário existente.
Gerenciar Status de Usuários: Pode Desativar uma conta de usuário (impedindo o login, mas mantendo o histórico de pedidos) ou Reativar uma conta previamente desativada.
Manutenção do Sistema:
Backup do Banco de Dados: Com um único clique, pode baixar um arquivo de backup (.db) contendo todos os dados do sistema (usuários, pedidos, itens, etc.), garantindo a segurança das informações.
Como Executar o Projeto
1. Configuração Inicial
Certifique-se de ter o Python 3 instalado.
Instale as dependências necessárias:
Configure as credenciais de e-mail no arquivo secrets.toml.
2. Execução Local
Na primeira vez, execute o script do banco de dados para criar as tabelas e o administrador principal:
Inicie o aplicativo Streamlit:
3. Acesso via Web
O sistema pode ser implantado no Streamlit Community Cloud para acesso global via navegador em qualquer dispositivo (desktop ou mobile).
