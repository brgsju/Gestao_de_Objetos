from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin , current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from werkzeug.middleware.proxy_fix import ProxyFix
from oauthlib.oauth2 import WebApplicationClient
import os, json, requests

# Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None) # Need to set this environment var to work
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None) # Need to set this environment var to work
GOOGLE_DISCOVERY_URL = ("https://accounts.google.com/.well-known/openid-configuration")
# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

#import json

# Criação do app em flask
app = Flask(__name__)
app.config['SECRET_KEY'] = '9OLWxND4o83j4K4iuopO'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///projeto.db.sqlite'
app.app_context().push()
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)

# Base de dados
db = SQLAlchemy()
db.init_app(app)

migrate = Migrate(app, db)

# Definicao da tabela de usuários na base de dados 
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy7
    nome = db.Column(db.String(25))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    department = db.Column(db.String(1000))
    role = db.Column(db.String(50), default="usuario")  # Novo campo para o tipo de usuário

##### LOGIN COM O GOOGLE
# helper to retrieve google auth uri
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

@app.route("/glogin")
def glogin():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri='https://www.dcc.ufrrj.br' + url_for('callback'),
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route("/gcallback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send a request to get tokens! Yay tokens!
    print(request.url, request.base_url)
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url.replace('http://', 'https://', 1),
        redirect_url='https://www.dcc.ufrrj.br' + url_for('callback'),
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    print(unique_id, users_name, users_email)
    print(userinfo_response.json())
    # Create a user in your db with the information provided
    # by Google
    #user = User(
    #    id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    #)

    # tenta pegar usuário, caso já exista
    user = User.query.filter_by(email=users_email).first()

    # Doesn't exist? Add it to the database.
    #if not User.get(unique_id):
    if not user:
        #User.create(unique_id, users_name, users_email, picture)
        user = User(nome=users_name,email=users_email, department="DCC")
        db.session.add(user)
        db.session.commit()

    # Begin user session by logging the user in
    login_user(user)

    if user.role == "secretario":
       return redirect(url_for('secretarios', email=users_email))  # Redireciona para a página inicial após o login
    else:
        return redirect(url_for('usuarios', email=users_email))  # Redireciona para a página inicial após o login

##### END LOGIN COM O GOOGLE


@login_manager.user_loader
def load_user(user_id):
    # since the email is the primary key of our user table, use it in the query for the user
    return User.query.get(int(user_id))

@app.route("/") 
def homepage():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"]) # Agora aceita tanto GET quanto POST
def login():
    if request.method == "POST":
        # Lógica de autenticação aqui
        email = request.form.get('email')
        password = request.form.get('password')
        # procura este usuario na base de dados
        # se existir, o objeto "user" será uma estrutura de dados contendo os dados do usuario que vieram da base de dados
        user = User.query.filter_by(email=email).first()
        print(user)
        # verifica se usuario existe
        # pega a senha fornecida, calcula o hash e compara com o hash guardado no banco de dados

        # PRECISA INFORMAR ERRO !!!!!!!!!!!!!!
        if not user or not check_password_hash(user.password, password):
            flash("Email ou senha incorreta!", "error")  # Mensagem de erro flash
            return redirect(url_for('login')) # if user doesn't exist or password is wrong, reload the page

        login_user(user)

        if user.role == "secretario":
           return redirect(url_for('secretarios', email=email))  # Redireciona para a página inicial após o login
        else:
            return redirect(url_for('usuarios', email=email))  # Redireciona para a página inicial após o login
   
        # se chegou aqui, o usuário é valido
     
    return render_template("login.html") 


@app.route("/usuarios/<email>")
@login_required
def usuarios(email):

    # Teste necessario se tiver a tela de completar o cadastro
    #if (current_user.department == "")
    #    return redirect(url_for('completa_cadastro', email=email))

    user = User.query.filter_by(email=email).first_or_404()
    nome = user.nome
    # Equipamentos disponíveis (não alugados)
    available_equipamentos = db.session.query(Equipamento.tipo).distinct().all()
    
    # Equipamentos reservados pelo usuário atual (futuro)
    today_date = datetime.today().strftime('%d/%m/%Y')

    reserved_equipamentos = Agendamento.query.filter(
        Agendamento.user_id == user.id,
        Agendamento.devolucao == False,
        Agendamento.data >= today_date
    ).all()

    
    # Equipamentos utilizados e não devolvidos (pendentes)
    pending_equipamentos = Agendamento.query.filter(
        Agendamento.user_id == user.id,
        Agendamento.devolucao == False,
        Agendamento.data < today_date
    ).all()
    
    # Equipamentos já utilizados e devolvidos (histórico)
    returned_equipamentos = Agendamento.query.filter_by(user_id=user.id, devolucao=True).all()
    
    return render_template("usuarios.html", 
                           nome_usuario= nome, 
                           available_equipamentos=available_equipamentos,
                           reserved_equipamentos=reserved_equipamentos,
                           pending_equipamentos=pending_equipamentos,
                           returned_equipamentos=returned_equipamentos)

@app.route("/secretarios/<email>")
@login_required
def secretarios(email):
    if current_user.role != "secretario":
        flash("Apenas secretários têm permissão para acessar esta página.", "error_permissao")
        return redirect(url_for('login'))
    
    user = User.query.filter_by(email=email).first_or_404()

    # Equipamentos disponíveis (não alugados)
    equipamentos = Equipamento.query.filter(Equipamento.existe == True).all()
    
    # Equipamentos reservados pelo usuário atual (futuro)
    today_date = datetime.today().strftime('%d/%m/%Y')
    reserved_equipamentos = Agendamento.query.filter(
        Agendamento.user_id == user.id,
        Agendamento.devolucao == False,
        Agendamento.data >= today_date
    ).all()
    
    # Equipamentos utilizados e não devolvidos (pendentes)
    pending_equipamentos = Agendamento.query.filter(
        Agendamento.user_id == user.id,
        Agendamento.devolucao == False,
        Agendamento.data < today_date
    ).all()
    nome = user.nome
        
    # Equipamentos reservados (futuro)
    today_date = datetime.today().strftime('%d/%m/%Y')
    reserved_equipamentos = db.session.query(Agendamento, User, Equipamento).join(User).join(Equipamento).filter(
        Agendamento.devolucao == False,
        Agendamento.data >= today_date
    ).all()
    
    # Equipamentos utilizados e não devolvidos (pendentes)
    pending_equipamentos = db.session.query(Agendamento, User, Equipamento).join(User).join(Equipamento).filter(
        Agendamento.devolucao == False,
        Agendamento.data < today_date
    ).all()

    return render_template("secretarios.html", nome_usuario= nome, 
                           reserved_equipamentos=reserved_equipamentos,
                           pending_equipamentos=pending_equipamentos, equipamentos=equipamentos)



@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        department = request.form["department"]

        user = User.query.filter_by(email=username).first() # if this returns a user, then the email already exists in database

        if user: # if a user is found, we want to redirect back to signup page so user can try again  
            return redirect(url_for('cadastro'))

        # create new user with the form data. Hash the password so plaintext version isn't saved.
        new_user = User(nome = username,email=email, password=generate_password_hash(password, method='pbkdf2'), department=department)
        #new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'), admin=admin)

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        #usuario = {'username': username, 'password': password, 'department': department}
        #salvar_usuario(usuario)
        #return "Usuário cadastrado com sucesso!"

        return redirect(url_for("login"))

    return render_template("cadastro.html") 

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

#---------------------------------------------------------------------------------------------------------------

# Definicao da tabela de equipamentos na base de dados 
class Equipamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(100), nullable=False) #datashow/pc/piloto
    modelo =  db.Column(db.String(100)) # e20 2.0
    marca =  db.Column(db.String(100)) # epson / dell 
    description = db.Column(db.String(1000))
    existe = db.Column(db.Boolean, nullable=False , default=True)


class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10), nullable=False)  # Exemplo de formato: "2024-05-22"
    horario_inicio = db.Column(db.String(5), nullable=False)  # Exemplo de formato: "15:30"
    horario_fim = db.Column(db.String(5), nullable=False)  # Exemplo de formato: "15:30"
    equipamento_id = db.Column(db.Integer, db.ForeignKey('equipamento.id'), nullable=False)
    devolucao = db.Column(db.Boolean, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    equipamento = db.relationship('Equipamento', backref=db.backref('agendamentos', lazy=True))
    user = db.relationship('User', backref=db.backref('agendamentos', lazy=True))

@app.route("/add_equipamento", methods=["GET", "POST"])
@login_required
def add_equipamento():
    if current_user.role != "secretario":
        flash("Apenas secretários têm permissão para acessar esta página.", "error_permissao")
        return redirect(url_for('login'))
    
    if request.method == "POST":
        tipo = request.form["name"]
        modelo = request.form["modelo"]
        marca = request.form["marca"]
        description = request.form["description"]

        # Adicionar novo equipamento ao banco de dado
        
        new_equipamento = Equipamento( tipo=tipo , description=description , marca=marca, modelo=modelo)
        db.session.add(new_equipamento)
        db.session.commit()
        
        flash('Equipamento adicionado com sucesso!', 'success')

        return redirect(url_for('secretarios', email=current_user.email))  # Redireciona para a página inicial após o login

    return render_template("add_equipamento.html")

@app.route("/add_agendamento", methods=["GET", "POST"])
@login_required
def add_agendamento():
    if request.method == "POST":
        data = request.form["data"]
        data_hora_inicio = request.form["horario_inicio"]
        data_hora_fim  = request.form["horario_fim"]
        equipamento_tipo = request.form["equipamento_tipo"]
        user_id = current_user.id  # ID do usuário atual logado

        

        #data = datetime.strptime(data, '%Y-%m-%d')
        
        print(data)
        
        # Criação dos objetos datetime usando a data formatada corretamente
        data_hora_inicio = datetime.strptime(f"{data} {data_hora_inicio}", '%Y-%m-%d %H:%M')
        data_hora_fim = datetime.strptime(f"{data} {data_hora_fim}", '%Y-%m-%d %H:%M')

        print(data_hora_inicio)


        # Verificar se a data de fim é depois da data de início
        if data_hora_fim <= data_hora_inicio:
            flash("Erro: O horário de término deve ser posterior ao horário de início.", "error")
            return redirect(url_for('add_agendamento'))
        
        equipamento_disponivel = None
        equipamentos_do_tipo = Equipamento.query.filter_by(tipo=equipamento_tipo).all()
        for equipamento in equipamentos_do_tipo:
            conflito_agendamento = Agendamento.query.filter(
                Agendamento.equipamento_id == equipamento.id,
                Agendamento.data == data,
                Agendamento.horario_inicio < data_hora_fim,
                Agendamento.horario_fim > data_hora_inicio
            ).first()
            
            if not conflito_agendamento:
                equipamento_disponivel = equipamento
                break

        if conflito_agendamento:
            flash("Conflito de agendamento: já existe um agendamento para este horário.", "error")
        else:
            # Adicionar novo agendamento ao banco de dados
            new_agendamento = Agendamento(
                data=data,
                horario_inicio=data_hora_inicio.time().isoformat(),
                horario_fim=data_hora_fim.time().isoformat(),
                equipamento_id=equipamento_disponivel.id,
                devolucao=False,
                user_id=user_id
            )
            db.session.add(new_agendamento)
            db.session.commit()

            return redirect(url_for('usuarios', email=current_user.email))

    # Obtém todos os equipamentos disponíveis para exibir no formulário
    available_equipamentos = db.session.query(Equipamento.tipo).distinct().all()

    return render_template("add_agendamento.html", available_equipamentos=available_equipamentos)

@app.route("/cancelar_reserva/<int:agendamento_id>", methods=["POST"])
@login_required
def cancelar_reserva(agendamento_id):
    agendamento = Agendamento.query.get_or_404(agendamento_id)
    
    # Verifica se o usuário logado é o dono da reserva
    if agendamento.user_id != current_user.id:
        return "Você não tem permissão para cancelar esta reserva.", 403
    
    db.session.delete(agendamento)
    db.session.commit()
    
    return redirect(url_for('usuarios', email=current_user.email))

@app.route("/cadastro_secretario", methods=["GET", "POST"])
@login_required
def cadastro_secretario():
    if not current_user.is_secretario:
        return "Você não tem permissão para adicionar novos secretários.", 403

    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        department = request.form["department"]

        user = User.query.filter_by(email=username).first() # if this returns a user, then the email already exists in database

        if user: # if a user is found, we want to redirect back to signup page so user can try again  
            return redirect(url_for('cadastro_secretario'))

        # create new user with the form data. Hash the password so plaintext version isn't saved.
        new_user = User(
            nome=username,
            email=email,
            password=generate_password_hash(password, method='pbkdf2'),
            department=department,
            is_secretario=True  # Define como secretário
        )

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("cadastro_secretario.html")
@app.route('/editar_equipamento/<int:equipamento_id>', methods=['GET', 'POST'])
@login_required
def editar_equipamento(equipamento_id):
    equipamento = Equipamento.query.get_or_404(equipamento_id)

    if request.method == 'POST':
        # Atualiza os dados do equipamento com os dados do formulário
        equipamento.tipo = request.form['name']
        equipamento.description = request.form['description']
        equipamento.modelo = request.form["modelo"]
        equipamento.marca = request.form["marca"]

        # Commit para salvar as alterações no banco de dados
        db.session.commit()

        flash('Equipamento atualizado com sucesso!', 'success')
        return redirect(url_for('secretarios', email=current_user.email))

    return render_template('editar_equipamento.html', equipamento=equipamento)

@app.route('/remover_equipamento/<int:equipamento_id>', methods=['POST'])
@login_required
def remover_equipamento(equipamento_id):
    equipamento = Equipamento.query.get_or_404(equipamento_id)
    equipamento.existe = False

    today_date = datetime.today().strftime('%d/%m/%Y')

    agendamentosFuturos = Agendamento.query.filter(
        Agendamento.equipamento_id == equipamento_id,
        Agendamento.data > today_date
    ).all()

    if agendamentosFuturos:
        flash('Atenção: Existem agendamentos futuros para este equipamento. Todos os agendamentos futuros serão excluídos.', 'warning')
    else:
        print("Nenhum agendamento futuro encontrado.")
    for agendamento in agendamentosFuturos:
        db.session.delete(agendamento)

    db.session.commit()

    flash('Equipamento removido com sucesso!', 'sucess')
    return redirect(url_for('secretarios', email=current_user.email))

@app.route("/devolucao/<int:agendamento_id>", methods=["POST"])
def devolucao(agendamento_id):
    agendamento = Agendamento.query.get_or_404(agendamento_id)
    agendamento.devolucao = True  
    db.session.commit()
    user_email = current_user.email  # Ou outra forma de obter o email do usuário atual

    return redirect(url_for('secretarios' , email=user_email))

if __name__ == "__main__":

    # Inicializar/atualizar base de dados antes de iniciar a aplicacao
    db.create_all()
    # Inicia a aplicacao
    app.run(debug=True)


    # Inicializar/atualizar base de dados antes de iniciar a aplicacao
    db.create_all()
    # Inicia a aplicacao
    app.run(debug=True)
