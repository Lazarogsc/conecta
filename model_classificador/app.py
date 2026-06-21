import sys
import os
import re
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from config import Config
from ia.model_local import classificar_local

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "info"
bcrypt = Bcrypt(app)

# ─── Models ───────────────────────────────────────────────────────────

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True)
    senha = db.Column(db.String(200))
    idade = db.Column(db.Integer)
    punido_ate = db.Column(db.DateTime, nullable=True)
    perfil_privado = db.Column(db.Boolean, default=False)
    tema = db.Column(db.String(10), default='claro')  # claro ou escuro

    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def has_pending_request_to(self, user):
        return FollowRequest.query.filter_by(from_user_id=self.id, to_user_id=user.id).first() is not None

    def pending_requests_count(self):
        return FollowRequest.query.filter_by(to_user_id=self.id).count()

    def unread_notifications_count(self):
        return Notification.query.filter_by(user_id=self.id, lida=False).count()

    def followers_count(self):
        return self.followers.count()

    def following_count(self):
        return self.followed.count()

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text)
    classificacao_local = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    data_publicacao = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)

    author = db.relationship('User', backref=db.backref('posts', lazy=True, cascade="all, delete-orphan"))

    @property
    def likes_users(self):
        return [like.user_id for like in PostLike.query.filter_by(post_id=self.id).all()]

    @property
    def comments(self):
        return Comment.query.filter_by(post_id=self.id, parent_id=None).order_by(Comment.data.asc()).all()

class PostLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.Column(db.Integer, default=0)

    author = db.relationship('User', backref=db.backref('comments', lazy=True))
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

    @property
    def likes_users(self):
        return [cl.user_id for cl in CommentLike.query.filter_by(comment_id=self.id).all()]

class CommentLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'))

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tipo = db.Column(db.String(30), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(300), nullable=True)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    lida = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))

class FollowRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)

    from_user = db.relationship('User', foreign_keys=[from_user_id], backref='sent_requests')
    to_user = db.relationship('User', foreign_keys=[to_user_id], backref='received_requests')

# ─── Helpers ───────────────────────────────────────────────────────────

# Duração da suspensão temporária aplicada a perfis menores que tentam
# publicar conteúdo classificado como adulto (medida protetiva e educativa).
SUSPENSAO_MENOR_MINUTOS = 5

MENSAGEM_BLOQUEIO_MENOR = (
    "Esta publicação foi bloqueada por conter conteúdo possivelmente impróprio "
    "para a sua faixa etária. Esta é uma medida protetiva e educativa, voltada à sua segurança."
)


def criar_notificacao(user_id, tipo, mensagem, link=None):
    if user_id == getattr(current_user, 'id', None):
        return
    notif = Notification(user_id=user_id, tipo=tipo, mensagem=mensagem, link=link)
    db.session.add(notif)


def suspender_menor(user):
    """Aplica suspensão temporária ao perfil menor e registra a notificação.

    Centraliza a regra de moderação reutilizada na publicação, nos comentários
    e nas respostas, evitando duplicação. O commit fica a cargo do chamador.
    """
    user.punido_ate = datetime.utcnow() + timedelta(minutes=SUSPENSAO_MENOR_MINUTOS)
    criar_notificacao(user.id, 'punishment', MENSAGEM_BLOQUEIO_MENOR)

def validar_senha(senha):
    """Valida senha conforme boas práticas LGPD (Art. 46 - segurança)."""
    erros = []
    if len(senha) < 8:
        erros.append("A senha deve ter no mínimo 8 caracteres.")
    if not re.search(r'[A-Z]', senha):
        erros.append("A senha deve conter pelo menos uma letra maiúscula.")
    if not re.search(r'[a-z]', senha):
        erros.append("A senha deve conter pelo menos uma letra minúscula.")
    if not re.search(r'[0-9]', senha):
        erros.append("A senha deve conter pelo menos um número.")
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', senha):
        erros.append("A senha deve conter pelo menos um caractere especial (!@#$%...).")
    return erros

def gerar_username(nome, email):
    """Gera um username único baseado no nome."""
    base = re.sub(r'[^a-z0-9]', '', nome.lower().split()[0]) if nome else email.split('@')[0]
    username = base
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base}{counter}"
        counter += 1
    return username

def calcular_trending():
    """Retorna os 5 posts com mais engajamento (likes + comentários) nas últimas 24h."""
    limite = datetime.utcnow() - timedelta(hours=24)
    posts = Post.query.filter(Post.data_publicacao >= limite).all()
    if not posts:
        # Fallback: pega os 5 mais engajados de todos os tempos
        posts = Post.query.all()
    if not posts:
        return []
    # Ordenar por engajamento (likes + comments)
    posts_sorted = sorted(posts, key=lambda p: p.likes + p.comments_count, reverse=True)
    return posts_sorted[:5]

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ─── Routes ───────────────────────────────────────────────────────────

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("feed"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")
        idade = int(request.form.get("idade", 0))
        username_input = request.form.get("username", "").strip().lower()

        # Validar username
        username_input = re.sub(r'[^a-z0-9_.]', '', username_input)
        if len(username_input) < 3:
            username_input = gerar_username(nome, email)

        if User.query.filter_by(username=username_input).first():
            flash("Este nome de usuário já está em uso.", "error")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("Este e-mail já está cadastrado.", "error")
            return render_template("register.html")

        # Validar senha (LGPD Art. 46)
        erros_senha = validar_senha(senha)
        if erros_senha:
            for err in erros_senha:
                flash(err, "error")
            return render_template("register.html")

        if idade < 1 or idade > 120:
            flash("Idade inválida.", "error")
            return render_template("register.html")

        senha_hash = bcrypt.generate_password_hash(senha).decode("utf-8")
        user = User(
            nome=nome, email=email, senha=senha_hash,
            idade=idade, username=username_input
        )
        db.session.add(user)
        db.session.commit()

        # Auto-login após registro
        login_user(user)
        flash(f"Bem-vindo(a) à Conecta, {nome.split()[0]}! 🎉", "success")
        return redirect(url_for("feed"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()
        if user and bcrypt.check_password_hash(user.senha, request.form["senha"]):
            login_user(user)
            return redirect(url_for("feed"))
        flash("E-mail ou senha incorretos.", "error")
    return render_template("login.html")

@app.route("/feed")
@login_required
def feed():
    if current_user.idade < 18:
        posts = Post.query.filter(Post.classificacao_local != 'adulto').order_by(Post.data_publicacao.desc()).all()
    else:
        posts = Post.query.order_by(Post.data_publicacao.desc()).all()

    sugestoes = User.query.filter(User.id != current_user.id).limit(6).all()
    sugestoes = [u for u in sugestoes if not current_user.is_following(u)]

    trending = calcular_trending()
    notif_count = current_user.unread_notifications_count()

    return render_template("feed.html", posts=posts, sugestoes=sugestoes[:4],
                           trending=trending, notif_count=notif_count)

@app.route("/publicar", methods=["GET", "POST"])
@login_required
def publicar():
    if current_user.punido_ate and current_user.punido_ate > datetime.utcnow():
        segundos = int((current_user.punido_ate - datetime.utcnow()).total_seconds())
        minutos = segundos // 60
        flash(f"Você está suspenso(a). Aguarde {minutos} min e {segundos % 60}s.", "error")
        return redirect(request.referrer or url_for("feed"))

    if request.method == "POST":
        texto = request.form.get("texto")
        if not texto:
            return redirect(request.referrer or url_for("feed"))

        local = classificar_local(texto)

        if current_user.idade < 18 and local == "adulto":
            suspender_menor(current_user)
            db.session.commit()
            flash(MENSAGEM_BLOQUEIO_MENOR, "error")
            return redirect(request.referrer or url_for("feed"))

        post = Post(
            texto=texto, classificacao_local=local,
            user_id=current_user.id, data_publicacao=datetime.utcnow(),
            likes=0, comments_count=0
        )
        db.session.add(post)
        db.session.commit()
        return redirect(request.referrer or url_for("feed"))

    return redirect(url_for("feed"))

@app.route("/like/<int:post_id>", methods=["POST"])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    already_liked = PostLike.query.filter_by(user_id=current_user.id, post_id=post_id).first()

    if already_liked:
        db.session.delete(already_liked)
        post.likes = max(0, post.likes - 1)
        action = "unliked"
    else:
        new_like = PostLike(user_id=current_user.id, post_id=post_id)
        db.session.add(new_like)
        post.likes += 1
        action = "liked"
        criar_notificacao(
            post.user_id, 'like',
            f'❤️ {current_user.nome} curtiu sua publicação.',
            link=f'/post/{post_id}'
        )

    db.session.commit()
    return jsonify({"likes": post.likes, "action": action})

# ─── Comentários (com moderação para menores) ────────────────────────

@app.route("/comment/<int:post_id>", methods=["POST"])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    texto = request.form.get("texto", "").strip()
    if not texto:
        return jsonify({"error": "Comentário vazio"}), 400

    # MODERAÇÃO: classificar comentário de menores
    if current_user.idade < 18:
        if current_user.punido_ate and current_user.punido_ate > datetime.utcnow():
            return jsonify({"error": "Você está suspenso(a) temporariamente."}), 403

        resultado = classificar_local(texto)
        if resultado == "adulto":
            suspender_menor(current_user)
            db.session.commit()
            return jsonify({"error": MENSAGEM_BLOQUEIO_MENOR}), 403

    comment = Comment(
        texto=texto, user_id=current_user.id,
        post_id=post_id, data=datetime.utcnow()
    )
    db.session.add(comment)
    post.comments_count = Comment.query.filter_by(post_id=post_id).count() + 1

    criar_notificacao(
        post.user_id, 'comment',
        f'💬 {current_user.nome} comentou: "{texto[:50]}{"..." if len(texto) > 50 else ""}"',
        link=f'/post/{post_id}'
    )

    db.session.commit()

    return jsonify({
        "id": comment.id, "texto": comment.texto,
        "author_nome": current_user.nome,
        "author_inicial": current_user.nome[0].upper(),
        "author_username": current_user.username,
        "data": "agora", "likes": 0, "replies": [],
        "comments_count": post.comments_count
    })

@app.route("/comment/reply/<int:comment_id>", methods=["POST"])
@login_required
def reply_comment(comment_id):
    parent = Comment.query.get_or_404(comment_id)
    texto = request.form.get("texto", "").strip()
    if not texto:
        return jsonify({"error": "Resposta vazia"}), 400

    # MODERAÇÃO de respostas de menores
    if current_user.idade < 18:
        resultado = classificar_local(texto)
        if resultado == "adulto":
            suspender_menor(current_user)
            db.session.commit()
            return jsonify({"error": MENSAGEM_BLOQUEIO_MENOR}), 403

    reply = Comment(
        texto=texto, user_id=current_user.id,
        post_id=parent.post_id, parent_id=comment_id,
        data=datetime.utcnow()
    )
    db.session.add(reply)

    post = Post.query.get(parent.post_id)
    post.comments_count = Comment.query.filter_by(post_id=parent.post_id).count() + 1

    criar_notificacao(
        parent.user_id, 'comment',
        f'💬 {current_user.nome} respondeu: "{texto[:50]}{"..." if len(texto) > 50 else ""}"',
        link=f'/post/{parent.post_id}'
    )

    db.session.commit()

    return jsonify({
        "id": reply.id, "texto": reply.texto,
        "author_nome": current_user.nome,
        "author_inicial": current_user.nome[0].upper(),
        "author_username": current_user.username,
        "data": "agora", "likes": 0,
        "comments_count": post.comments_count
    })

@app.route("/comment/like/<int:comment_id>", methods=["POST"])
@login_required
def like_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    already_liked = CommentLike.query.filter_by(user_id=current_user.id, comment_id=comment_id).first()

    if already_liked:
        db.session.delete(already_liked)
        comment.likes = max(0, comment.likes - 1)
        action = "unliked"
    else:
        new_like = CommentLike(user_id=current_user.id, comment_id=comment_id)
        db.session.add(new_like)
        comment.likes += 1
        action = "liked"
        criar_notificacao(
            comment.user_id, 'like',
            f'❤️ {current_user.nome} curtiu seu comentário.',
            link=f'/post/{comment.post_id}'
        )

    db.session.commit()
    return jsonify({"likes": comment.likes, "action": action})

@app.route("/comments/<int:post_id>")
@login_required
def get_comments(post_id):
    comments = Comment.query.filter_by(post_id=post_id, parent_id=None).order_by(Comment.data.asc()).all()

    def serialize(c):
        return {
            "id": c.id, "texto": c.texto,
            "author_nome": c.author.nome if c.author else "Desconhecido",
            "author_inicial": c.author.nome[0].upper() if c.author else "?",
            "author_username": c.author.username if c.author else "",
            "data": timeago_filter(c.data),
            "likes": c.likes,
            "liked_by_me": current_user.id in c.likes_users,
            "replies": [serialize(r) for r in c.replies.order_by(Comment.data.asc()).all()]
        }

    return jsonify([serialize(c) for c in comments])

# ─── Post Individual ─────────────────────────────────────────────────

@app.route("/post/<int:post_id>")
@login_required
def post_view(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template("post_view.html", post=post)

# ─── Apagar Post ─────────────────────────────────────────────────────

@app.route("/apagar/<int:post_id>", methods=["POST"])
@login_required
def apagar(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id == current_user.id:
        Comment.query.filter_by(post_id=post_id).delete()
        PostLike.query.filter_by(post_id=post_id).delete()
        db.session.delete(post)
        db.session.commit()
        flash("Publicação apagada.", "success")
    return redirect(request.referrer or url_for("feed"))

# ─── Seguir / Deixar de seguir ───────────────────────────────────────

@app.route("/seguir/<int:user_id>", methods=["POST"])
@login_required
def seguir(user_id):
    user_to_follow = User.query.get_or_404(user_id)
    if current_user.id == user_to_follow.id:
        return redirect(request.referrer or url_for("feed"))
    if current_user.is_following(user_to_follow):
        return redirect(request.referrer or url_for("feed"))

    # Se perfil é privado, criar solicitação
    if user_to_follow.perfil_privado:
        existing = FollowRequest.query.filter_by(
            from_user_id=current_user.id, to_user_id=user_to_follow.id
        ).first()
        if not existing:
            req = FollowRequest(from_user_id=current_user.id, to_user_id=user_to_follow.id)
            db.session.add(req)
            criar_notificacao(
                user_to_follow.id, 'follow_request',
                f'🔒 @{current_user.username} quer seguir você.',
                link=f'/perfil'
            )
            db.session.commit()
            flash("Solicitação enviada! Aguarde aprovação.", "info")
    else:
        current_user.followed.append(user_to_follow)
        criar_notificacao(
            user_to_follow.id, 'follow',
            f'👤 @{current_user.username} começou a seguir você!',
            link=f'/usuario/{current_user.username}'
        )
        db.session.commit()
    return redirect(request.referrer or url_for("feed"))

@app.route("/unfollow/<int:user_id>", methods=["POST"])
@login_required
def unfollow(user_id):
    user_to_unfollow = User.query.get_or_404(user_id)
    if current_user.is_following(user_to_unfollow):
        current_user.followed.remove(user_to_unfollow)
        db.session.commit()
    return redirect(request.referrer or url_for("feed"))

# ─── Follow Requests (Perfil Privado) ────────────────────────────────

@app.route("/follow-requests")
@login_required
def follow_requests():
    reqs = FollowRequest.query.filter_by(to_user_id=current_user.id).all()
    return jsonify([{
        "id": r.id,
        "from_user_id": r.from_user_id,
        "username": r.from_user.username,
        "nome": r.from_user.nome,
        "inicial": r.from_user.nome[0].upper(),
        "data": timeago_filter(r.data)
    } for r in reqs])

@app.route("/follow-request/<int:request_id>/accept", methods=["POST"])
@login_required
def accept_follow_request(request_id):
    req = FollowRequest.query.get_or_404(request_id)
    if req.to_user_id != current_user.id:
        return jsonify({"error": "Não autorizado"}), 403
    # Adicionar como seguidor
    req.from_user.followed.append(current_user)
    criar_notificacao(
        req.from_user_id, 'follow',
        f'✅ @{current_user.username} aceitou sua solicitação!',
        link=f'/usuario/{current_user.username}'
    )
    db.session.delete(req)
    db.session.commit()
    return jsonify({"ok": True})

@app.route("/follow-request/<int:request_id>/reject", methods=["POST"])
@login_required
def reject_follow_request(request_id):
    req = FollowRequest.query.get_or_404(request_id)
    if req.to_user_id != current_user.id:
        return jsonify({"error": "Não autorizado"}), 403
    criar_notificacao(
        req.from_user_id, 'follow',
        f'❌ @{current_user.username} recusou sua solicitação.',
        link=f'/usuario/{current_user.username}'
    )
    db.session.delete(req)
    db.session.commit()
    return jsonify({"ok": True})

# ─── Perfil ──────────────────────────────────────────────────────────

@app.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    if request.method == "POST":
        acao = request.form.get("acao")
        if acao == "toggle_privado":
            current_user.perfil_privado = not current_user.perfil_privado
            db.session.commit()
            flash("Perfil atualizado.", "success")
        elif acao == "mudar_tema":
            tema = request.form.get("tema", "claro")
            current_user.tema = tema
            db.session.commit()
        return redirect(url_for("perfil"))

    notif_count = current_user.unread_notifications_count()
    meus_posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.data_publicacao.desc()).all()
    seguidores = current_user.followers.all()
    seguindo = current_user.followed.all()

    return render_template("perfil.html", notif_count=notif_count,
                           meus_posts=meus_posts, seguidores=seguidores, seguindo=seguindo)

# ─── Ver perfil de outro usuário ─────────────────────────────────────

@app.route("/usuario/<username>")
@login_required
def ver_usuario(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.data_publicacao.desc()).all()
    if current_user.idade < 18:
        posts = [p for p in posts if p.classificacao_local != 'adulto']
    notif_count = current_user.unread_notifications_count()
    return render_template("ver_usuario.html", usuario=user, posts=posts, notif_count=notif_count)

# ─── Menções - Buscar usuários que sigo ──────────────────────────────

@app.route("/api/mencoes")
@login_required
def api_mencoes():
    q = request.args.get("q", "").strip().lower()
    seguidos = current_user.followed.all()
    resultado = []
    for u in seguidos:
        if q in u.nome.lower() or q in u.username.lower():
            resultado.append({"id": u.id, "nome": u.nome, "username": u.username})
    return jsonify(resultado[:10])

# ─── Notificações ────────────────────────────────────────────────────

@app.route("/notificacoes")
@login_required
def notificacoes():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.data.desc()).limit(50).all()
    return jsonify([{
        "id": n.id, "tipo": n.tipo, "mensagem": n.mensagem,
        "link": n.link, "data": timeago_filter(n.data), "lida": n.lida
    } for n in notifs])

@app.route("/notificacoes/ler", methods=["POST"])
@login_required
def marcar_notificacoes_lidas():
    Notification.query.filter_by(user_id=current_user.id, lida=False).update({"lida": True})
    db.session.commit()
    return jsonify({"ok": True})

@app.route("/notificacoes/ler/<int:notif_id>", methods=["POST"])
@login_required
def marcar_notificacao_lida(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id == current_user.id:
        notif.lida = True
        db.session.commit()
    return jsonify({"ok": True})

# ─── Busca ───────────────────────────────────────────────────────────

@app.route("/busca")
@login_required
def busca():
    q = request.args.get("q", "").strip()
    filtro = request.args.get("filtro", "tudo")  # tudo, usuarios, publicacoes
    if not q:
        return redirect(url_for("feed"))

    usuarios_encontrados = []
    posts = []

    if filtro in ("tudo", "usuarios"):
        usuarios_encontrados = User.query.filter(
            (User.nome.ilike(f"%{q}%")) | (User.username.ilike(f"%{q}%"))
        ).limit(10).all()

    if filtro in ("tudo", "publicacoes"):
        posts = Post.query.filter(Post.texto.ilike(f"%{q}%")).order_by(Post.data_publicacao.desc()).all()
        if current_user.idade < 18:
            posts = [p for p in posts if p.classificacao_local != 'adulto']

    sugestoes = User.query.filter(User.id != current_user.id).limit(6).all()
    sugestoes = [u for u in sugestoes if not current_user.is_following(u)]
    trending = calcular_trending()
    notif_count = current_user.unread_notifications_count()

    return render_template("feed.html", posts=posts, sugestoes=sugestoes[:4],
                           trending=trending, notif_count=notif_count,
                           busca_query=q, filtro=filtro,
                           usuarios_encontrados=usuarios_encontrados)

# ─── Páginas Legais ──────────────────────────────────────────────────

@app.route("/privacidade")
def privacidade():
    return render_template("privacidade.html")

@app.route("/termos")
def termos():
    return render_template("termos.html")

@app.route("/seguranca")
def seguranca():
    return render_template("seguranca.html")

# ─── Logout ──────────────────────────────────────────────────────────

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ─── Template Filters ────────────────────────────────────────────────

@app.template_filter('timeago')
def timeago_filter(dt):
    if not dt:
        return ""
    now = datetime.utcnow()
    diff = now - dt
    if diff.days > 0:
        return f"{diff.days}d"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600}h"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60}m"
    else:
        return "agora"

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    # O modo debug é controlado pela variável de ambiente FLASK_DEBUG (ver config.py).
    app.run(debug=app.config.get("DEBUG", False))
