# Sistema de Gestão de Equipamentos Acadêmicos

Este repositório contém o código para um Sistema de Gestão de Equipamentos Acadêmicos, desenvolvido para facilitar o gerenciamento e a utilização de equipamentos por professores da Universidade Federal Rural do Rio de Janeiro (UFRRJ).

<img src="https://github.com/BeatrizGama/projeto-sistema-de-emprestimo/blob/main/imagens/tela_usuario.png" alt="Interface do Sistema">

# Links úteis

[Slides de Apresentação](https://docs.google.com/presentation/d/1fk3FtyziLQ8HwEc3S26_IQIGIyQTguarllFB54ai1T4/edit?slide=id.p#slide=id.p)

[Relatório do Projeto](https://docs.google.com/document/d/15BoMjhosllfrjL4XQJzzj7SmcGjs_-mi/edit?tab=t.0#heading=h.gjdgxs)

# Autores

- Júlia da Silva Borges
- Beatriz Fernandes Gama de Lima
- Bruna de Andrade da Silva
- Bruna Luísa Costa Reis dos Santos

**Data de Início:** 24/03 - **Data de Encerramento:** 24/06

# Descrição

Este projeto foi criado para solucionar problemas na distribuição e agendamento de equipamentos acadêmicos. O sistema permite que professores e secretários realizem reservas, gerenciem equipamentos, visualizem agendamentos e muito mais, tudo de forma intuitiva e eficiente.

# Instalações

## Pré-Requisitos

Certifique-se de ter o Python 3.xeo pip instalado em seu ambiente. Além disso, será necessário o gerenciador de pacotes `virtualenv` .

## Passos para instalação

1. Clone o repositório:
```
git clone https://github.com/seu-usuario/sistema-gestao-equipamentos.git
cd sistema-gestao-equipamentos
```
2. Crie e ative um Ambiente Virtual:
```
python -m venv venv
source venv/bin/activate  # No Windows use `venv\Scripts\activate`
```

3. Instalar dependências:

```
pip install -r requirements.txt
```

4. Configurar o Banco de Dados:

```
flask db init
flask db migrate
flask db upgrade
```

5. Executar uma aplicação:

```
flask run
```

## Bibliotecas Utilizadas

- Flask: Framework web leve para Python.
- Flask-Login: Gerenciamento de sessões de login do usuário.
- Flask-SQLAlchemy: Integração do SQLAlchemy com o Flask.
- Flask-Migrate: Gerenciamento de migrações de banco de dados para SQLAlchemy.
- Werkzeug: Utilitários para WSGI e aplicações web

# Uso

Após seguir os passos de instalação, uma aplicação estará disponível emhttp://127.0.0.1:5000/ . A partir daí, você pode acessar as diversas funcionalidades do sistema, como cadastro, login, agendamento de equipamentos, entre outros.

## Páginas Principais

- `/`: Redireciona para a página de login.
- `/login`: Página de login.
- `/usuarios/<email>`: Painel para usuários.
- `/secretarios/<email>`: Dashboard para secretários.
- `/cadastro`: Página de cadastro de novos usuários.
- `/add_equipamento`: Formulário para adicionar novos equipamentos.
- `/add_agendamento`: Formulário para agendar equipamentos.
