from flask import Flask, Response, render_template, make_response, request
from markupsafe import escape
from flask import render_template
from flask import request

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/cad/usuario")
def usuario():
    return render_template('user.html', titulo="Cadastro de Usuario")

@app.route("/cad/caduser", methods=["POST"])
def caduser():
    return request.form


@app.route("/cad/anuncios", methods=["GET", "POST"])
def anuncios():
    if request.method == "POST":
        titulo = request.form.get("titulo")
        descricao = request.form.get("descricao")
        valor = request.form.get("valor")
        print("Anúncio cadastrado:", titulo, descricao, valor)
        return "Anúncio cadastrado com sucesso"
    return render_template('anuncios.html')


@app.route("/anuncios/pergunta", methods=["GET", "POST"])
def pergunta():
    if request.method == "POST":
        texto = request.form.get("texto")
        print("Pergunta feita:", texto)
        return "Pergunta enviada com sucesso"
    return render_template("pergunta.html")


@app.route("/anuncios/compra", methods=["GET", "POST"])
def compra():
    if request.method == "POST":
        id_anuncio = request.form.get("id_anuncio")
        id_usuario = request.form.get("id_usuario")
        print("Compra realizada:", id_usuario, id_anuncio)
        return "Compra realizada com sucesso"
    return render_template("compra.html")


@app.route("/anuncios/favoritos")
def favoritos():
    print("favorito inserido")
    return f"<h4>Comprado</h4> "

@app.route("/config/categoria", methods=["GET", "POST"])
def categoria():
    if request.method == "POST":
        nome_categoria = request.form.get("nome_categoria")
        print("Categoria cadastrada:", nome_categoria)
        return "Categoria cadastrada com sucesso"
    return render_template("categoria.html")


@app.route("/relatorios/vendas")
def relVendas():
    return render_template('relVendas.html')

@app.route("/relatorios/compras")
def relCompras():
    return render_template('relCompras.html')
