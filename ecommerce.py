from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from decimal import Decimal

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"  # necessário p/ flash()

# Ajuste sua conexão se mudar usuário/senha/porta/banco
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
#   HELPERS / CONFIRMAÇÃO
# =========================

def render_confirm_delete(titulo, mensagem, action_url, cancel_url):
    return render_template(
        "confirm_delete.html",
        titulo=titulo,
        mensagem=mensagem,
        action_url=action_url,
        cancel_url=cancel_url
    )

def get_or_create_default_category():
    """Garante a existência da categoria 'Sem categoria' e retorna ela."""
    default = Categoria.query.filter_by(nome="Sem categoria").first()
    if not default:
        default = Categoria(nome="Sem categoria")
        db.session.add(default)
        db.session.commit()  # precisamos do ID
    return default


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
    nome  = request.form.get("user")  or request.form.get("nome")
    email = request.form.get("email")
    senha = request.form.get("passwd") or request.form.get("senha")

    if not (nome and email and senha):
        flash("Preencha nome, e-mail e senha.")
        return redirect(url_for("usuario"))

    if Usuario.query.filter_by(email=email).first():
        flash("Este e-mail já está cadastrado.")
        return redirect(url_for("usuario"))

    try:
        u = Usuario(nome=nome, email=email, senha=senha)
        db.session.add(u)
        db.session.commit()
        flash("Usuário cadastrado com sucesso!")
    except IntegrityError:
        db.session.rollback()
        flash("E-mail já cadastrado.")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro inesperado ao cadastrar usuário: {e}")
    return redirect(url_for("usuario"))

@app.route("/usuario/editar/<int:id>", methods=["GET", "POST"])
def editarusuario(id):
    u = Usuario.query.get_or_404(id)
    if request.method == "POST":
        novo_nome  = request.form.get("user")  or request.form.get("nome")
        novo_email = request.form.get("email")
        nova_senha = request.form.get("passwd") or request.form.get("senha")

        if not (novo_nome and novo_email and nova_senha):
            flash("Preencha nome, e-mail e senha.")
            return redirect(url_for("editarusuario", id=id))

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
            flash("E-mail já cadastrado.")
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar usuário: {e}")
        return redirect(url_for("editarusuario", id=id))

    return render_template("eusuario.html", usuario=u, titulo="Usuário")

@app.route("/usuario/deletar/<int:id>", methods=["GET", "POST"])
def deletarusuario(id):
    u = Usuario.query.get_or_404(id)
    if request.method == "GET":
        return render_confirm_delete(
            "Deletar Usuário",
            f"Tem certeza que deseja excluir o usuário <b>{u.nome}</b>?",
            url_for("deletarusuario", id=id),
            url_for("usuario"),
        )

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
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao cadastrar categoria: {e}")
        return redirect(url_for("categoria"))

    categorias = Categoria.query.order_by(Categoria.id.desc()).all()
    return render_template("categoria.html", categorias=categorias, titulo="Categoria")

@app.route("/categoria/editar/<int:id>", methods=["GET","POST"])
def editarcategoria(id):
    c = Categoria.query.get_or_404(id)
    if request.method == "POST":
        nome = request.form.get("nome")
        if not nome:
            flash("Informe o nome.")
            return redirect(url_for("editarcategoria", id=id))

        if nome != c.nome and Categoria.query.filter_by(nome=nome).first():
            flash("Já existe uma categoria com esse nome.")
            return redirect(url_for("editarcategoria", id=id))

        try:
            c.nome = nome
            db.session.commit()
            flash("Categoria atualizada!")
            return redirect(url_for("categoria"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar: {e}")
            return redirect(url_for("editarcategoria", id=id))

    return render_template("ecategoria.html", categoria=c, titulo="Categoria")

@app.route("/categoria/deletar/<int:id>", methods=["GET","POST"])
def deletarcategoria(id):
    c = Categoria.query.get_or_404(id)

    # Não permitir excluir a categoria "Sem categoria"
    if c.nome.lower().strip() == "sem categoria":
        flash("Você não pode excluir a categoria padrão 'Sem categoria'.", "danger")
        return redirect(url_for("categoria"))

    if request.method == "GET":
        # Mensagem de confirmação já explicando o que vai acontecer
        return render_confirm_delete(
            "Deletar Categoria",
            f"Ao excluir a categoria <b>{c.nome}</b>, os anúncios vinculados serão movidos para <b>Sem categoria</b>. Deseja continuar?",
            url_for("deletarcategoria", id=id),
            url_for("categoria")
        )

    # POST: mover anúncios e excluir a categoria
    try:
        default_cat = get_or_create_default_category()

        # move todos os anúncios desta categoria para a default
        Anuncio.query.filter_by(categoria_id=c.id).update(
            {"categoria_id": default_cat.id}
        )
        db.session.commit()

        # agora pode excluir a categoria
        db.session.delete(c)
        db.session.commit()
        flash("Categoria deletada. Anúncios remanescentes foram movidos para 'Sem categoria'.")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao deletar categoria: {e}", "danger")
    return redirect(url_for("categoria"))


# ----------- ANÚNCIO -----------
@app.route("/cad/anuncios", methods=["GET", "POST"])
def anuncios():
    if request.method == "POST":
        titulo       = request.form.get("titulo")    or request.form.get("nome")
        descricao    = request.form.get("descricao") or request.form.get("desc")
        valor_str    = request.form.get("valor")     or request.form.get("preco")
        categoria_id = request.form.get("categoria_id") or request.form.get("cat")
        usuario_id   = request.form.get("usuario_id")   or request.form.get("uso")

        if not (titulo and valor_str and categoria_id and usuario_id):
            flash("Preencha título/nome, preço/valor, categoria e usuário.")
            return redirect(url_for("anuncios"))

        try:
            valor = Decimal((valor_str or "0").replace(",", "."))
        except:
            flash("Preço inválido.")
            return redirect(url_for("anuncios"))

        categoria = Categoria.query.get(int(categoria_id))
        if not categoria:
            flash("Categoria não encontrada.")
            return redirect(url_for("anuncios"))

        usuario = Usuario.query.get(int(usuario_id))
        if not usuario:
            flash("Usuário não encontrado.")
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
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao cadastrar anúncio: {e}")
        return redirect(url_for("anuncios"))

    lista_anuncios = Anuncio.query.order_by(Anuncio.id.desc()).all()
    categorias = Categoria.query.order_by(Categoria.nome.asc()).all()
    usuarios = Usuario.query.order_by(Usuario.nome.asc()).all()
    return render_template('anuncios.html', titulo="Anúncio",
                           anuncios=lista_anuncios, categorias=categorias, usuarios=usuarios)

@app.route("/anuncio/editar/<int:id>", methods=["GET","POST"])
def editaranuncio(id):
    a = Anuncio.query.get_or_404(id)
    if request.method == "POST":
        titulo    = request.form.get("nome") or request.form.get("titulo")
        descricao = request.form.get("desc") or request.form.get("descricao")
        preco_str = request.form.get("preco") or request.form.get("valor")
        cat_id    = request.form.get("cat") or request.form.get("categoria_id")
        uso_id    = request.form.get("uso") or request.form.get("usuario_id")

        if not (titulo and preco_str and cat_id and uso_id):
            flash("Preencha nome/título, preço, categoria e usuário.")
            return redirect(url_for("editaranuncio", id=id))

        try:
            preco = Decimal((preco_str or "0").replace(",", "."))
        except:
            flash("Preço inválido.")
            return redirect(url_for("editaranuncio", id=id))

        categoria = Categoria.query.get(int(cat_id))
        usuario   = Usuario.query.get(int(uso_id))
        if not categoria or not usuario:
            flash("Categoria ou usuário inválidos.")
            return redirect(url_for("editaranuncio", id=id))

        try:
            a.titulo = titulo
            a.descricao = descricao
            a.preco = preco
            a.categoria_id = categoria.id
            a.usuario_id   = usuario.id
            db.session.commit()
            flash("Anúncio atualizado!")
            return redirect(url_for("anuncios"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar anúncio: {e}")
            return redirect(url_for("editaranuncio", id=id))

    categorias = Categoria.query.order_by(Categoria.nome.asc()).all()
    usuarios = Usuario.query.order_by(Usuario.nome.asc()).all()
    return render_template("eanuncio.html", anuncio=a, categorias=categorias, usuarios=usuarios)

@app.route("/anuncio/deletar/<int:id>", methods=["GET","POST"])
def deletaranuncio(id):
    a = Anuncio.query.get_or_404(id)
    if request.method == "GET":
        return render_confirm_delete(
            "Deletar Anúncio",
            f"Tem certeza que deseja excluir o anúncio <b>{a.titulo}</b>?",
            url_for("deletaranuncio", id=id),
            url_for("anuncios")
        )
    try:
        db.session.delete(a)
        db.session.commit()
        flash("Anúncio deletado.")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao deletar anúncio: {e}")
    return redirect(url_for("anuncios"))


# ----------- PERGUNTA -----------
@app.route("/anuncios/pergunta", methods=["GET", "POST"])
def pergunta():
    if request.method == "POST":
        anuncio_id = request.form.get("anuncio_id")
        usuario_id = request.form.get("usuario_id")
        texto      = request.form.get("texto")

        if not (anuncio_id and usuario_id and texto):
            flash("Preencha anuncio_id, usuario_id e texto.")
            return redirect(url_for("pergunta"))

        anuncio = Anuncio.query.get(int(anuncio_id))
        usuario = Usuario.query.get(int(usuario_id))
        if not anuncio or not usuario:
            flash("Anúncio ou usuário inválido.")
            return redirect(url_for("pergunta"))

        try:
            p = Pergunta(anuncio_id=anuncio.id, usuario_id=usuario.id, texto=texto)
            db.session.add(p)
            db.session.commit()
            flash("Pergunta enviada com sucesso!")
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar pergunta: {e}")
        return redirect(url_for("pergunta"))

    perguntas = Pergunta.query.order_by(Pergunta.id.desc()).all()
    anuncios  = Anuncio.query.order_by(Anuncio.titulo.asc()).all()
    usuarios  = Usuario.query.order_by(Usuario.nome.asc()).all()
    return render_template("pergunta.html", perguntas=perguntas, anuncios=anuncios, usuarios=usuarios)

@app.route("/pergunta/editar/<int:id>", methods=["GET","POST"])
def editarpergunta(id):
    p = Pergunta.query.get_or_404(id)
    if request.method == "POST":
        texto    = request.form.get("texto")
        resposta = request.form.get("resposta")
        if not texto:
            flash("Informe o texto.")
            return redirect(url_for("editarpergunta", id=id))
        try:
            p.texto = texto
            p.resposta = resposta
            db.session.commit()
            flash("Pergunta atualizada!")
            return redirect(url_for("pergunta"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar: {e}")
            return redirect(url_for("editarpergunta", id=id))
    return render_template("epergunta.html", perg=p)

@app.route("/pergunta/deletar/<int:id>", methods=["GET","POST"])
def deletarpergunta(id):
    p = Pergunta.query.get_or_404(id)
    if request.method == "GET":
        return render_confirm_delete(
            "Deletar Pergunta",
            f"Tem certeza que deseja excluir esta pergunta?",
            url_for("deletarpergunta", id=id),
            url_for("pergunta")
        )
    try:
        db.session.delete(p)
        db.session.commit()
        flash("Pergunta deletada.")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao deletar: {e}")
    return redirect(url_for("pergunta"))


# ----------- COMPRA -----------
@app.route("/anuncios/compra", methods=["GET", "POST"])
def compra():
    if request.method == "POST":
        anuncio_id = request.form.get("anuncio_id")
        usuario_id = request.form.get("usuario_id")
        quantidade = request.form.get("quantidade", "1")

        if not (anuncio_id and usuario_id):
            flash("Preencha anuncio_id e usuario_id.")
            return redirect(url_for("compra"))

        anuncio = Anuncio.query.get(int(anuncio_id))
        usuario = Usuario.query.get(int(usuario_id))
        if not anuncio or not usuario:
            flash("Anúncio ou usuário inválido.")
            return redirect(url_for("compra"))

        try:
            qtd   = int(quantidade)
            total = anuncio.preco * qtd

            c = Compra(usuario_id=usuario.id, anuncio_id=anuncio.id, quantidade=qtd, total=total)
            db.session.add(c)
            db.session.commit()
            flash("Compra realizada com sucesso!")
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao registrar compra: {e}")
        return redirect(url_for("compra"))

    compras = Compra.query.order_by(Compra.id.desc()).all()
    anuncios = Anuncio.query.order_by(Anuncio.titulo.asc()).all()
    usuarios = Usuario.query.order_by(Usuario.nome.asc()).all()
    return render_template("compra.html", compras=compras, anuncios=anuncios, usuarios=usuarios)

@app.route("/compras/editar/<int:id>", methods=["GET","POST"])
def editarcompra(id):
    c = Compra.query.get_or_404(id)
    if request.method == "POST":
        quantidade = int(request.form.get("quantidade", "1"))
        if quantidade < 1:
            flash("Quantidade inválida.")
            return redirect(url_for("editarcompra", id=id))
        try:
            c.quantidade = quantidade
            c.total = c.anuncio.preco * quantidade
            db.session.commit()
            flash("Compra atualizada!")
            return redirect(url_for("compra"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar: {e}")
            return redirect(url_for("editarcompra", id=id))
    return render_template("ecompra.html", compra=c)

@app.route("/compras/deletar/<int:id>", methods=["GET","POST"])
def deletarcompra(id):
    c = Compra.query.get_or_404(id)
    if request.method == "GET":
        return render_confirm_delete(
            "Deletar Compra",
            f"Tem certeza que deseja excluir a compra #{c.id}?",
            url_for("deletarcompra", id=id),
            url_for("compra")
        )
    try:
        db.session.delete(c)
        db.session.commit()
        flash("Compra deletada.")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao deletar: {e}")
    return redirect(url_for("compra"))


# ----------- RELATÓRIOS (placeholders) -----------
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
