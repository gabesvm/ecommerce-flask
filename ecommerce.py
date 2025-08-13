from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from decimal import Decimal

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"  # necessário para flash()

# Ajuste sua conexão aqui se mudar usuário/senha/porta/banco
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:150874bb11@localhost:3306/ecommerce'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =========================
#        MODELOS
# =========================

class Usuario(db.Model):
    __tablename__ = "usuario"
    id        = db.Column(db.Integer, primary_key=True)
    nome      = db.Column(db.String(120), nullable=False)
    email     = db.Column(db.String(120), unique=True, nullable=False)
    senha     = db.Column(db.String(255), nullable=False)
    criado_em = db.Column(db.DateTime, server_default=db.func.now())

    anuncios  = db.relationship("Anuncio",  back_populates="usuario", cascade="all, delete-orphan")
    perguntas = db.relationship("Pergunta", back_populates="usuario", cascade="all, delete-orphan")
    compras   = db.relationship("Compra",   back_populates="usuario", cascade="all, delete-orphan")


class Categoria(db.Model):
    __tablename__ = "categoria"
    id   = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)

    anuncios = db.relationship("Anuncio", back_populates="categoria")


class Anuncio(db.Model):
    __tablename__ = "anuncio"
    id           = db.Column(db.Integer, primary_key=True)
    titulo       = db.Column(db.String(150), nullable=False)
    descricao    = db.Column(db.Text)
    preco        = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    categoria_id = db.Column(db.Integer, db.ForeignKey("categoria.id"), nullable=False, index=True)
    usuario_id   = db.Column(db.Integer, db.ForeignKey("usuario.id"),   nullable=False, index=True)
    criado_em    = db.Column(db.DateTime, server_default=db.func.now())

    categoria = db.relationship("Categoria", back_populates="anuncios")
    usuario   = db.relationship("Usuario",   back_populates="anuncios")
    perguntas = db.relationship("Pergunta",  back_populates="anuncio", cascade="all, delete-orphan")
    compras   = db.relationship("Compra",    back_populates="anuncio", cascade="all, delete-orphan")


class Compra(db.Model):
    __tablename__ = "compra"
    id         = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False, index=True)
    anuncio_id = db.Column(db.Integer, db.ForeignKey("anuncio.id"), nullable=False, index=True)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    total      = db.Column(db.Numeric(10, 2), nullable=False)
    criado_em  = db.Column(db.DateTime, server_default=db.func.now())

    usuario = db.relationship("Usuario", back_populates="compras")
    anuncio = db.relationship("Anuncio", back_populates="compras")


class Pergunta(db.Model):
    __tablename__ = "pergunta"
    id         = db.Column(db.Integer, primary_key=True)
    anuncio_id = db.Column(db.Integer, db.ForeignKey("anuncio.id"), nullable=False, index=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False, index=True)
    texto      = db.Column(db.Text, nullable=False)
    resposta   = db.Column(db.Text)
    criado_em  = db.Column(db.DateTime, server_default=db.func.now())

    anuncio = db.relationship("Anuncio", back_populates="perguntas")
    usuario = db.relationship("Usuario", back_populates="perguntas")


# =========================
#          ROTAS
# =========================

@app.route("/")
def index():
    return render_template('index.html')


# ----------- USUÁRIO -----------
@app.route("/cad/usuario")
def usuario():
    usuarios = Usuario.query.order_by(Usuario.id.desc()).all()
    return render_template('user.html', titulo="Usuário", usuarios=usuarios)

@app.route("/usuario/criar", methods=["POST"])
def criarusuario():
    # aceita tanto (user/email/passwd) quanto (nome/email/senha)
    nome  = request.form.get("user")   or request.form.get("nome")
    email = request.form.get("email")
    senha = request.form.get("passwd") or request.form.get("senha")

    if not (nome and email and senha):
        flash("Preencha nome, e-mail e senha.")
        return redirect(url_for("usuario"))

    # e-mail único
    if Usuario.query.filter_by(email=email).first():
        flash("Este e-mail já está cadastrado. Use outro ou edite o usuário existente.")
        return redirect(url_for("usuario"))

    try:
        u = Usuario(nome=nome, email=email, senha=senha)
        db.session.add(u)
        db.session.commit()
        flash("Usuário cadastrado com sucesso!")
        return redirect(url_for("usuario"))
    except IntegrityError:
        db.session.rollback()
        flash("E-mail já cadastrado. Por favor, use outro e-mail.")
        return redirect(url_for("usuario"))
    except Exception as e:
        db.session.rollback()
        flash(f"Erro inesperado ao cadastrar usuário: {e}")
        return redirect(url_for("usuario"))

@app.route("/usuario/detalhar/<int:id>")
def buscarusuario(id):
    u = Usuario.query.get_or_404(id)
    return u.nome

@app.route("/usuario/editar/<int:id>", methods=["GET", "POST"])
def editarusuario(id):
    u = Usuario.query.get_or_404(id)
    if request.method == "POST":
        novo_nome  = request.form.get("user")   or request.form.get("nome")
        novo_email = request.form.get("email")
        nova_senha = request.form.get("passwd") or request.form.get("senha")

        if not (novo_nome and novo_email and nova_senha):
            flash("Preencha nome, e-mail e senha.")
            return redirect(url_for("editarusuario", id=id))

        # se trocar e-mail, checar unicidade
        if novo_email != u.email and Usuario.query.filter_by(email=novo_email).first():
            flash("Este e-mail já está em uso por outro usuário.")
            return redirect(url_for("editarusuario", id=id))

        try:
            u.nome = novo_nome
            u.email = novo_email
            u.senha = nova_senha
            db.session.commit()
            flash("Usuário atualizado!")
            return redirect(url_for("usuario"))
        except IntegrityError:
            db.session.rollback()
            flash("E-mail já cadastrado. Por favor, use outro e-mail.")
            return redirect(url_for("editarusuario", id=id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar usuário: {e}")
            return redirect(url_for("editarusuario", id=id))

    return render_template("eusuario.html", usuario=u, titulo="Usuário")

@app.route("/usuario/deletar/<int:id>")
def deletarusuario(id):
    u = Usuario.query.get_or_404(id)
    try:
        db.session.delete(u)
        db.session.commit()
        flash("Usuário deletado.")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao deletar usuário: {e}")
    return redirect(url_for("usuario"))


# ----------- CATEGORIA -----------
@app.route("/config/categoria", methods=["GET", "POST"])
def categoria():
    if request.method == "POST":
        nome_categoria = request.form.get("nome") or request.form.get("nome_categoria")
        if not nome_categoria:
            flash("Informe o nome da categoria.")
            return redirect(url_for("categoria"))

        if Categoria.query.filter_by(nome=nome_categoria).first():
            flash("Categoria já existe.")
            return redirect(url_for("categoria"))

        try:
            cat = Categoria(nome=nome_categoria)
            db.session.add(cat)
            db.session.commit()
            flash("Categoria cadastrada com sucesso!")
            return redirect(url_for("categoria"))
        except IntegrityError:
            db.session.rollback()
            flash("Categoria já existe.")
            return redirect(url_for("categoria"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao cadastrar categoria: {e}")
            return redirect(url_for("categoria"))

    categorias = Categoria.query.order_by(Categoria.id.desc()).all()
    return render_template("categoria.html", categorias=categorias, titulo="Categoria")

# rota compatível com o caminho do professor (se usar em algum template)
@app.route("/categoria/novo", methods=["POST"])
def novacategoria():
    nome_categoria = request.form.get("nome") or request.form.get("nome_categoria")
    if not nome_categoria:
        flash("Informe o nome da categoria.")
        return redirect(url_for("categoria"))
    try:
        if Categoria.query.filter_by(nome=nome_categoria).first():
            flash("Categoria já existe.")
            return redirect(url_for("categoria"))
        cat = Categoria(nome=nome_categoria)
        db.session.add(cat)
        db.session.commit()
        flash("Categoria cadastrada com sucesso!")
        return redirect(url_for("categoria"))
    except IntegrityError:
        db.session.rollback()
        flash("Categoria já existe.")
        return redirect(url_for("categoria"))
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao cadastrar categoria: {e}")
        return redirect(url_for("categoria"))


# ----------- ANÚNCIO -----------
@app.route("/cad/anuncios", methods=["GET", "POST"])
def anuncios():
    if request.method == "POST":
        # aceita nomes do professor OU do teu template
        titulo       = request.form.get("titulo")    or request.form.get("nome")
        descricao    = request.form.get("descricao") or request.form.get("desc")
        valor_str    = request.form.get("valor")     or request.form.get("preco")
        categoria_id = request.form.get("categoria_id") or request.form.get("cat")
        usuario_id   = request.form.get("usuario_id")   or request.form.get("uso")

        if not (titulo and valor_str and categoria_id and usuario_id):
            flash("Preencha título/nome, preço/valor, categoria e usuário.")
            return redirect(url_for("anuncios"))

        # preço
        try:
            valor = Decimal((valor_str or "0").replace(",", "."))
        except:
            flash("Preço inválido.")
            return redirect(url_for("anuncios"))

        # valida FK: categoria e usuário precisam existir
        categoria = Categoria.query.get(int(categoria_id))
        if not categoria:
            flash("Categoria não encontrada. Selecione uma categoria válida.")
            return redirect(url_for("anuncios"))

        usuario = Usuario.query.get(int(usuario_id))
        if not usuario:
            flash("Usuário não encontrado. Selecione um usuário válido.")
            return redirect(url_for("anuncios"))

        try:
            a = Anuncio(
                titulo=titulo,
                descricao=descricao,
                preco=valor,
                categoria_id=categoria.id,
                usuario_id=usuario.id,
            )
            db.session.add(a)
            db.session.commit()
            flash("Anúncio cadastrado com sucesso!")
            return redirect(url_for("anuncios"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao cadastrar anúncio: {e}")
            return redirect(url_for("anuncios"))

    # GET: carregar anúncios + listas para os selects
    lista_anuncios = Anuncio.query.order_by(Anuncio.id.desc()).all()
    categorias = Categoria.query.order_by(Categoria.nome.asc()).all()
    usuarios = Usuario.query.order_by(Usuario.nome.asc()).all()
    return render_template(
        'anuncios.html',
        titulo="Anúncio",
        anuncios=lista_anuncios,
        categorias=categorias,
        usuarios=usuarios
    )


# ----------- PERGUNTA / COMPRA / FAVORITOS -----------
@app.route("/anuncios/pergunta", methods=["GET", "POST"])
def pergunta():
    if request.method == "POST":
        anuncio_id = request.form.get("anuncio_id")
        usuario_id = request.form.get("usuario_id")
        texto      = request.form.get("texto")

        if not (anuncio_id and usuario_id and texto):
            flash("Preencha anuncio_id, usuario_id e texto.")
            return redirect(url_for("pergunta"))

        try:
            p = Pergunta(anuncio_id=int(anuncio_id), usuario_id=int(usuario_id), texto=texto)
            db.session.add(p)
            db.session.commit()
            flash("Pergunta enviada com sucesso!")
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar pergunta: {e}")
        return redirect(url_for("pergunta"))

    return render_template("pergunta.html")


@app.route("/anuncios/compra", methods=["GET", "POST"])
def compra():
    if request.method == "POST":
        anuncio_id = request.form.get("anuncio_id")
        usuario_id = request.form.get("usuario_id")
        quantidade = request.form.get("quantidade", "1")

        if not (anuncio_id and usuario_id):
            flash("Preencha anuncio_id e usuario_id.")
            return redirect(url_for("compra"))

        try:
            anuncio = Anuncio.query.get(int(anuncio_id))
            if not anuncio:
                flash("Anúncio não encontrado.")
                return redirect(url_for("compra"))

            qtd   = int(quantidade)
            total = anuncio.preco * qtd

            c = Compra(
                usuario_id=int(usuario_id),
                anuncio_id=int(anuncio_id),
                quantidade=qtd,
                total=total
            )
            db.session.add(c)
            db.session.commit()
            flash("Compra realizada com sucesso!")
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao registrar compra: {e}")
        return redirect(url_for("compra"))

    return render_template("compra.html")


@app.route("/anuncios/favoritos")
def favoritos():
    return "<h4>Favorito inserido</h4>"


# ----------- RELATÓRIOS -----------
@app.route("/relatorios/vendas")
def relVendas():
    return render_template('relVendas.html')

@app.route("/relatorios/compras")
def relCompras():
    return render_template('relCompras.html')


# Para rodar direto com: python ecommerce.py (opcional)
if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
