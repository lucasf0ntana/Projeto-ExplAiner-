import json
import re
from datetime import date, datetime, timedelta
from flask import Blueprint, jsonify, request, session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.security import check_password_hash, generate_password_hash

from models.database import db
from models.model_aluno import Aluno
from models.model_tema import Tema
from models.model_desafio import Desafio
from models.model_questao import Questao
from models.model_desafio_questao import DesafioQuestao
from models.model_aluno_desafio import AlunoDesafio
from models.model_aprendizado import RespostaDesafio
from services.aprendizado.gerador_questoes import gerar_questoes

aprendizado_controller = Blueprint("aprendizado_controller", __name__)

QUANTIDADES_PERMITIDAS = {5, 10, 15, 20}
DIFICULDADES = {
    "facil": "Fácil", "fácil": "Fácil", "easy": "Fácil",
    "normal": "Normal", "medio": "Normal", "médio": "Normal",
    "dificil": "Difícil", "difícil": "Difícil", "hard": "Difícil",
}
PONTOS_POR_DIFICULDADE = {"Fácil": 10, "Normal": 15, "Difícil": 20}


def aluno_logado():
    aluno_id = session.get("aluno_id")
    return db.session.get(Aluno, aluno_id) if aluno_id else None


def erro_nao_autenticado():
    return jsonify({"erro": "Entre na sua conta para continuar."}), 401


def atualizar_sequencia_diaria(aluno):
    hoje = date.today()
    hoje_iso = hoje.isoformat()
    anterior = aluno.ultimo_dia_ativo
    if anterior != hoje_iso:
        if anterior:
            try:
                data_anterior = date.fromisoformat(anterior)
                aluno.sequencia_atual = (aluno.sequencia_atual or aluno.foguinho or 0) + 1 if data_anterior == hoje - timedelta(days=1) else 1
            except ValueError:
                aluno.sequencia_atual = 1
        else:
            aluno.sequencia_atual = 1
        aluno.ultimo_dia_ativo = hoje_iso
        aluno.foguinho = aluno.sequencia_atual
        aluno.melhor_sequencia = max(aluno.melhor_sequencia or 0, aluno.sequencia_atual)


def progresso_do_aluno(aluno):
    desafios = Desafio.query.join(AlunoDesafio, AlunoDesafio.id_desafio == Desafio.id_desafio).filter(
        AlunoDesafio.id_aluno == aluno.id_aluno, AlunoDesafio.concluido.is_(True)
    ).all()
    total_respondidas = RespostaDesafio.query.filter_by(id_aluno=aluno.id_aluno).count()
    total_corretas = RespostaDesafio.query.filter_by(id_aluno=aluno.id_aluno, correta=True).count()
    return {
        "desafios_concluidos": len(desafios),
        "questoes_respondidas": total_respondidas,
        "questoes_corretas": total_corretas,
        "precisao": round((total_corretas / total_respondidas) * 100) if total_respondidas else 0,
        "minutos_ativos": aluno.minutos_ativos or 0,
    }


def serializar_questao_para_jogo(questao):
    alternativas = {}
    if questao.alternativas_json:
        try:
            alternativas = json.loads(questao.alternativas_json)
        except json.JSONDecodeError:
            alternativas = {}
    # Nunca expõe a alternativa correta antes do envio da resposta.
    return {
        "id_questao": questao.id_questao,
        "enunciado": questao.enunciado,
        "alternativas": alternativas,
    }


def serializar_ranking(aluno_atual=None, limite=20):
    # O ranking global inclui somente contas reais que já participaram de ao menos uma questão.
    alunos_participantes = db.session.query(RespostaDesafio.id_aluno).distinct().subquery()
    alunos = (Aluno.query.filter(Aluno.id_aluno.in_(db.session.query(alunos_participantes.c.id_aluno)))
              .order_by(Aluno.pontos.desc(), Aluno.nome.asc()).all())
    resultado = []
    posicao_atual = None
    for posicao, aluno in enumerate(alunos, start=1):
        registro = {
            "posicao": posicao,
            "id_aluno": aluno.id_aluno,
            "nick": aluno.nick or aluno.nome,
            "pontos": aluno.pontos or 0,
            "sequencia_atual": aluno.sequencia_atual or aluno.foguinho or 0,
            "minutos_ativos": aluno.minutos_ativos or 0,
        }
        if aluno_atual and aluno.id_aluno == aluno_atual.id_aluno:
            posicao_atual = posicao
        if len(resultado) < limite or (aluno_atual and aluno.id_aluno == aluno_atual.id_aluno):
            resultado.append(registro)
    return {"itens": resultado[:limite], "posicao_usuario": posicao_atual, "total_alunos": len(alunos)}


@aprendizado_controller.post("/api/auth/register")
def registrar_conta():
    dados = request.get_json(silent=True) or {}
    nome = str(dados.get("nome", "")).strip()
    nick = str(dados.get("nick", "")).strip()
    email = str(dados.get("email", "")).strip().lower()
    senha = str(dados.get("senha", ""))
    if not nome or not email or not senha:
        return jsonify({"erro": "Preencha nome, e-mail e senha."}), 400
    if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
        return jsonify({"erro": "Informe um e-mail válido."}), 400
    if len(senha) < 8:
        return jsonify({"erro": "A senha deve ter pelo menos 8 caracteres."}), 400
    if len(nome) > 100 or len(nick or nome) > 40:
        return jsonify({"erro": "Nome ou nick excede o limite permitido."}), 400
    if Aluno.buscar_por_email(email):
        return jsonify({"erro": "Já existe uma conta com este e-mail."}), 409
    nascimento = dados.get("data_nascimento") or None
    try:
        data_nascimento = date.fromisoformat(nascimento) if nascimento else None
    except (TypeError, ValueError):
        return jsonify({"erro": "A data de nascimento é inválida."}), 400
    novo_aluno = Aluno(
        nome=nome,
        nick=(nick or nome)[:40],
        email=email,
        senha=generate_password_hash(senha),
        data_nascimento=data_nascimento,
        pontos=0,
        foguinho=0,
        minutos_ativos=0,
        sequencia_atual=0,
        melhor_sequencia=0,
    )
    try:
        db.session.add(novo_aluno)
        db.session.commit()
        session.clear()
        session["aluno_id"] = novo_aluno.id_aluno
        return jsonify({"aluno": novo_aluno.to_dict()}), 201
    except ValueError:
        db.session.rollback()
        return jsonify({"erro": "A data de nascimento é inválida."}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"erro": "Já existe uma conta com este e-mail."}), 409


@aprendizado_controller.post("/api/auth/login")
def entrar_conta():
    dados = request.get_json(silent=True) or {}
    email = str(dados.get("email", "")).strip().lower()
    senha = str(dados.get("senha", ""))
    aluno = Aluno.buscar_por_email(email)
    if aluno is None:
        return jsonify({"erro": "E-mail ou senha incorretos."}), 401
    senha_valida = False
    if aluno.senha and (aluno.senha.startswith("pbkdf2:") or alumno_hash(aluno.senha)):
        try:
            senha_valida = check_password_hash(aluno.senha, senha)
        except (ValueError, TypeError):
            senha_valida = False
    else:
        senha_valida = aluno.senha == senha
        if senha_valida:
            aluno.senha = generate_password_hash(senha)
            db.session.commit()
    if not senha_valida:
        return jsonify({"erro": "E-mail ou senha incorretos."}), 401
    session.clear()
    session["aluno_id"] = aluno.id_aluno
    db.session.commit()
    return jsonify({"aluno": aluno.to_dict(), "progresso": progresso_do_aluno(aluno)})


def alumno_hash(senha):
    # Compatibility with Werkzeug's scrypt hashes, used by newer installations.
    return senha.startswith("scrypt:")


@aprendizado_controller.post("/api/auth/logout")
def sair_conta():
    session.clear()
    return jsonify({"ok": True})




@aprendizado_controller.delete("/api/auth/delete-account")
def excluir_propria_conta():
    aluno = aluno_logado()
    if not aluno:
        return erro_nao_autenticado()
    dados = request.get_json(silent=True) or {}
    senha_informada = str(dados.get("senha", ""))
    senha_armazenada = aluno.senha or ""
    try:
        senha_valida = check_password_hash(senha_armazenada, senha_informada) if senha_armazenada.startswith(("pbkdf2:", "scrypt:")) else senha_armazenada == senha_informada
    except (ValueError, TypeError):
        senha_valida = False
    if not senha_valida:
        return jsonify({"erro": "Senha incorreta. A conta não foi excluída."}), 403
    try:
        # Remove primeiro os registros pertencentes ao aluno para respeitar as chaves estrangeiras.
        RespostaDesafio.query.filter_by(id_aluno=aluno.id_aluno).delete(synchronize_session=False)
        AlunoDesafio.query.filter_by(id_aluno=aluno.id_aluno).delete(synchronize_session=False)
        from models.model_ranking import Ranking
        Ranking.query.filter_by(id_aluno=aluno.id_aluno).delete(synchronize_session=False)
        desafios_proprios = Desafio.query.filter_by(id_aluno=aluno.id_aluno).all()
        for desafio in desafios_proprios:
            DesafioQuestao.query.filter_by(id_desafio=desafio.id_desafio).delete(synchronize_session=False)
            db.session.delete(desafio)
        db.session.delete(aluno)
        db.session.commit()
        session.clear()
        return jsonify({"ok": True})
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Não foi possível excluir a conta. Nenhum dado foi alterado."}), 500


@aprendizado_controller.get("/api/learning/me")
def minha_conta():
    aluno = aluno_logado()
    if not aluno:
        return erro_nao_autenticado()
    return jsonify({"aluno": aluno.to_dict(), "progresso": progresso_do_aluno(aluno)})


@aprendizado_controller.patch("/api/learning/profile")
def atualizar_perfil():
    aluno = aluno_logado()
    if not aluno:
        return erro_nao_autenticado()
    dados = request.get_json(silent=True) or {}
    nick = str(dados.get("nick", "")).strip()
    if not nick or len(nick) > 40:
        return jsonify({"erro": "O nick deve ter entre 1 e 40 caracteres."}), 400
    aluno.nick = nick
    db.session.commit()
    return jsonify({"aluno": aluno.to_dict()})


@aprendizado_controller.get("/api/learning/catalog")
def catalogo_estudo():
    temas = Tema.query.order_by(Tema.materia.asc(), Tema.nome.asc()).all()
    catalogo = {}
    for tema in temas:
        catalogo.setdefault(tema.materia, []).append({"id_tema": tema.id_tema, "nome": tema.nome})
    return jsonify({"materias": [{"nome": nome, "temas": lista} for nome, lista in catalogo.items()]})


@aprendizado_controller.get("/api/learning/active-challenge")
def desafio_em_andamento():
    """Retorna o desafio incompleto mais recente da conta autenticada."""
    aluno = aluno_logado()
    if not aluno:
        return erro_nao_autenticado()
    desafios = (Desafio.query.filter_by(id_aluno=aluno.id_aluno)
                .order_by(Desafio.id_desafio.desc()).all())
    for desafio in desafios:
        # Revisões são sessões independentes e nunca devem substituir a jornada normal.
        if (desafio.nome or "").startswith("[REFAZER] "):
            continue
        registro = AlunoDesafio.query.filter_by(id_aluno=aluno.id_aluno, id_desafio=desafio.id_desafio).first()
        if registro and registro.concluido:
            continue
        total = DesafioQuestao.query.filter_by(id_desafio=desafio.id_desafio).count()
        respondidas = RespostaDesafio.query.filter_by(id_aluno=aluno.id_aluno, id_desafio=desafio.id_desafio).count()
        if total and respondidas < total:
            tema = db.session.get(Tema, desafio.id_tema)
            relacoes = DesafioQuestao.query.filter_by(id_desafio=desafio.id_desafio).all()
            questoes = [serializar_questao_para_jogo(db.session.get(Questao, r.id_questao)) for r in relacoes]
            respostas = {str(r.id_questao): r.alternativa_escolhida for r in RespostaDesafio.query.filter_by(id_aluno=aluno.id_aluno, id_desafio=desafio.id_desafio).all()}
            return jsonify({"ativo": True, "desafio": desafio.to_dict(), "tema": tema.to_dict() if tema else None, "questoes": questoes, "respondidas": respostas})
    return jsonify({"ativo": False})


@aprendizado_controller.post("/api/learning/challenges")
def criar_desafio_jogavel():
    aluno = aluno_logado()
    if not aluno:
        return erro_nao_autenticado()
    dados = request.get_json(silent=True) or {}
    refazer = bool(dados.get("refazer", False))
    try:
        id_tema = int(dados.get("id_tema", 0))
        quantidade = int(dados.get("quantidade_questoes", 5))
    except (TypeError, ValueError):
        return jsonify({"erro": "Tema e quantidade precisam ser válidos."}), 400
    dificuldade_chave = str(dados.get("dificuldade", "normal")).strip().casefold()
    dificuldade = DIFICULDADES.get(dificuldade_chave)
    if quantidade not in QUANTIDADES_PERMITIDAS:
        return jsonify({"erro": "Escolha 5, 10, 15 ou 20 questões."}), 400
    if not dificuldade:
        return jsonify({"erro": "Escolha Fácil, Normal ou Difícil."}), 400
    tema = db.session.get(Tema, id_tema)
    if not tema:
        return jsonify({"erro": "O tema selecionado não existe."}), 404
    proximo_nivel = (db.session.query(db.func.max(Desafio.nivel_mapa))
        .join(AlunoDesafio, AlunoDesafio.id_desafio == Desafio.id_desafio)
        .filter(Desafio.id_tema == id_tema, AlunoDesafio.id_aluno == aluno.id_aluno, AlunoDesafio.concluido.is_(True), ~Desafio.nome.startswith("[REFAZER] "))
        .scalar() or 0) + 1
    try:
        # Evita repetir enunciados que este aluno já viu para o mesmo tema e dificuldade.
        # O gerador usa primeiro questões ainda não vistas e só reutiliza conteúdo se o banco acabar.
        enunciados_anteriores = []
        if not refazer:
            anteriores = (db.session.query(Questao.enunciado)
                .join(DesafioQuestao, DesafioQuestao.id_questao == Questao.id_questao)
                .join(Desafio, Desafio.id_desafio == DesafioQuestao.id_desafio)
                .filter(Desafio.id_aluno == aluno.id_aluno,
                        Desafio.id_tema == tema.id_tema,
                        Desafio.dificuldade == dificuldade,
                        ~Desafio.nome.startswith("[REFAZER] "))
                .distinct().all())
            enunciados_anteriores = [linha[0] for linha in anteriores if linha[0]]
        questoes_geradas, origem, aviso = gerar_questoes(
            tema.materia, tema.nome, dificuldade, quantidade,
            excluir_enunciados=enunciados_anteriores
        )
        desafio = Desafio(
            nome=(f"[REFAZER] {tema.nome} · Tentativa" if refazer else f"{tema.nome} · Fase {proximo_nivel}"),
            dificuldade=dificuldade,
            pontuacao=quantidade * PONTOS_POR_DIFICULDADE[dificuldade],
            quantidade_questoes=quantidade,
            data_criacao=date.today(),
            id_tema=tema.id_tema,
            id_aluno=aluno.id_aluno,
            nivel_mapa=proximo_nivel,
            origem_ia=(origem == "ia"),
        )
        db.session.add(desafio)
        db.session.flush()
        for item in questoes_geradas:
            questao = Questao(
                enunciado=item["enunciado"],
                alternativa_correta=item["alternativa_correta"],
                id_tema=tema.id_tema,
                alternativas_json=json.dumps(item["alternativas"], ensure_ascii=False),
                explicacao=item["explicacao"],
            )
            db.session.add(questao)
            db.session.flush()
            db.session.add(DesafioQuestao(id_desafio=desafio.id_desafio, id_questao=questao.id_questao))
        db.session.commit()
        return jsonify({
            "desafio": desafio.to_dict(),
            "tema": tema.to_dict(),
            "origem_questoes": origem,
            "aviso": aviso,
            "questoes": [
                {"id_questao": q.id_questao, "enunciado": q.enunciado, "alternativas": json.loads(q.alternativas_json or "{}")}
                for q in Questao.query.join(DesafioQuestao, Questao.id_questao == DesafioQuestao.id_questao).filter(DesafioQuestao.id_desafio == desafio.id_desafio).all()
            ],
        }), 201
    except RuntimeError as erro:
        db.session.rollback()
        return jsonify({"erro": str(erro)}), 502
    except (SQLAlchemyError, KeyError, ValueError) as erro:
        db.session.rollback()
        return jsonify({"erro": "Não foi possível criar o desafio. Verifique a configuração e tente novamente."}), 500


@aprendizado_controller.get("/api/learning/challenges/<int:id_desafio>")
def buscar_desafio_jogavel(id_desafio):
    aluno = aluno_logado()
    if not aluno:
        return erro_nao_autenticado()
    desafio = db.session.get(Desafio, id_desafio)
    if not desafio or desafio.id_aluno != aluno.id_aluno:
        return jsonify({"erro": "Desafio não encontrado para esta conta."}), 404
    relacoes = DesafioQuestao.query.filter_by(id_desafio=id_desafio).all()
    questoes = [serializar_questao_para_jogo(db.session.get(Questao, item.id_questao)) for item in relacoes]
    respostas = {r.id_questao: r.alternativa_escolhida for r in RespostaDesafio.query.filter_by(id_aluno=aluno.id_aluno, id_desafio=id_desafio).all()}
    return jsonify({"desafio": desafio.to_dict(), "questoes": questoes, "respondidas": respostas})


@aprendizado_controller.post("/api/learning/challenges/<int:id_desafio>/answer")
def responder_questao(id_desafio):
    aluno = aluno_logado()
    if not aluno:
        return erro_nao_autenticado()
    dados = request.get_json(silent=True) or {}
    try:
        id_questao = int(dados.get("id_questao", 0))
        segundos = max(0, min(int(dados.get("segundos_gastos", 0)), 3600))
    except (TypeError, ValueError):
        return jsonify({"erro": "Resposta ou tempo inválido."}), 400
    alternativa = str(dados.get("alternativa", "")).strip().upper()
    if alternativa not in {"A", "B", "C", "D"}:
        return jsonify({"erro": "Selecione uma alternativa válida."}), 400
    desafio = db.session.get(Desafio, id_desafio)
    questao = db.session.get(Questao, id_questao)
    if not desafio or desafio.id_aluno != aluno.id_aluno or not questao or not DesafioQuestao.query.filter_by(id_desafio=id_desafio, id_questao=id_questao).first():
        return jsonify({"erro": "Questão não pertence a um desafio desta conta."}), 404
    existente = RespostaDesafio.query.filter_by(id_aluno=aluno.id_aluno, id_desafio=id_desafio, id_questao=id_questao).first()
    if existente:
        return jsonify({
            "ja_respondida": True,
            "correta": existente.correta,
            "alternativa_correta": questao.alternativa_correta,
            "explicacao": questao.explicacao or "Revise o enunciado e compare as alternativas.",
            "pontos_ganhos": existente.pontos_ganhos,
            "pontos_totais": aluno.pontos or 0,
        })
    correta = alternativa == str(questao.alternativa_correta or "").upper()
    pontos = (PONTOS_POR_DIFICULDADE.get(desafio.dificuldade, 10) if correta else 0)
    if desafio.nome.startswith("[REFAZER] "):
        pontos = 0
    registro = RespostaDesafio(
        id_aluno=aluno.id_aluno,
        id_desafio=id_desafio,
        id_questao=id_questao,
        alternativa_escolhida=alternativa,
        correta=correta,
        pontos_ganhos=pontos,
        segundos_gastos=segundos,
    )
    db.session.add(registro)
    aluno.pontos = (aluno.pontos or 0) + pontos
    atualizar_sequencia_diaria(aluno)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"erro": "Esta questão já foi respondida.", "ja_respondida": True}), 409
    return jsonify({
        "correta": correta,
        "alternativa_correta": questao.alternativa_correta,
        "explicacao": questao.explicacao or "Revise o enunciado e compare as alternativas.",
        "pontos_ganhos": pontos,
        "pontos_totais": aluno.pontos,
    })


@aprendizado_controller.post("/api/learning/challenges/<int:id_desafio>/complete")
def concluir_desafio(id_desafio):
    aluno = aluno_logado()
    if not aluno:
        return erro_nao_autenticado()
    desafio = db.session.get(Desafio, id_desafio)
    if not desafio or desafio.id_aluno != aluno.id_aluno:
        return jsonify({"erro": "Desafio não encontrado para esta conta."}), 404
    relacoes = DesafioQuestao.query.filter_by(id_desafio=id_desafio).count()
    respostas = RespostaDesafio.query.filter_by(id_aluno=aluno.id_aluno, id_desafio=id_desafio).all()
    if len(respostas) < relacoes:
        return jsonify({"erro": "Responda todas as questões antes de concluir."}), 400
    corretas = sum(1 for resposta in respostas if resposta.correta)
    pontos_base = sum(resposta.pontos_ganhos for resposta in respostas)
    registro = db.session.get(AlunoDesafio, (aluno.id_aluno, id_desafio))
    bonus_perfeito = 0
    if not registro:
        registro = AlunoDesafio(id_aluno=aluno.id_aluno, id_desafio=id_desafio)
        db.session.add(registro)
    elif registro.concluido:
        return jsonify({
            "concluido": True,
            "questoes_corretas": corretas,
            "quantidade_questoes": relacoes,
            "pontos_ganhos": pontos_base,
            "pontos_totais": aluno.pontos or 0,
            "bonus_perfeito": 0,
            "progresso": progresso_do_aluno(aluno),
        })
    if corretas == relacoes and relacoes > 0 and not desafio.nome.startswith("[REFAZER] "):
        bonus_perfeito = 25
        aluno.pontos = (aluno.pontos or 0) + bonus_perfeito
    registro.data_realizacao = date.today()
    registro.pontuacao_obtida = pontos_base + bonus_perfeito
    registro.concluido = True
    atualizar_sequencia_diaria(aluno)
    db.session.commit()
    return jsonify({
        "concluido": True,
        "questoes_corretas": corretas,
        "quantidade_questoes": relacoes,
        "pontos_ganhos": pontos_base + bonus_perfeito,
        "pontos_totais": aluno.pontos or 0,
        "bonus_perfeito": bonus_perfeito,
        "progresso": progresso_do_aluno(aluno),
    })


@aprendizado_controller.post("/api/learning/activity")
def registrar_tempo_ativo():
    aluno = aluno_logado()
    if not aluno:
        return erro_nao_autenticado()
    dados = request.get_json(silent=True) or {}
    try:
        segundos = max(0, min(int(dados.get("segundos", 0)), 120))
    except (TypeError, ValueError):
        return jsonify({"erro": "Tempo inválido."}), 400
    # Guardamos minutos inteiros, acumulando o resto para não descartar heartbeats curtos.
    total_segundos = (aluno.minutos_ativos or 0) * 60 + segundos
    aluno.minutos_ativos = total_segundos // 60
    atualizar_sequencia_diaria(aluno)
    db.session.commit()
    return jsonify({"minutos_ativos": aluno.minutos_ativos, "sequencia_atual": aluno.sequencia_atual})


@aprendizado_controller.get("/api/learning/ranking")
def ranking_de_estudo():
    aluno = aluno_logado()
    limite = request.args.get("limite", default=20, type=int)
    limite = max(1, min(limite, 100))
    return jsonify(serializar_ranking(aluno, limite))


@aprendizado_controller.get("/api/learning/history")
def historico_estudo():
    aluno = aluno_logado()
    if not aluno:
        return erro_nao_autenticado()
    registros = AlunoDesafio.query.filter_by(id_aluno=aluno.id_aluno).order_by(AlunoDesafio.data_realizacao.desc().nullslast()).limit(30).all()
    resultado = []
    for registro in registros:
        desafio = db.session.get(Desafio, registro.id_desafio)
        tema = db.session.get(Tema, desafio.id_tema) if desafio and desafio.id_tema else None
        resultado.append({
            "id_desafio": registro.id_desafio,
            "id_tema": desafio.id_tema if desafio else None,
            "quantidade_questoes": desafio.quantidade_questoes if desafio else 5,
            "nome": desafio.nome if desafio else "Desafio removido",
            "modo_revisao": bool(desafio and (desafio.nome or "").startswith("[REFAZER] ")),
            "materia": tema.materia if tema else "—",
            "tema": tema.nome if tema else "—",
            "dificuldade": desafio.dificuldade if desafio else "—",
            "pontuacao_obtida": registro.pontuacao_obtida or 0,
            "concluido": bool(registro.concluido),
            "data_realizacao": registro.data_realizacao.isoformat() if registro.data_realizacao else None,
        })
    return jsonify({"historico": resultado})
