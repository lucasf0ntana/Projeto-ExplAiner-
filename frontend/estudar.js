const API_URL = '';
const LETRAS = ['A', 'B', 'C', 'D'];
const state = {
  aluno: null,
  progresso: null,
  catalogo: [],
  desafio: null,
  temaAtual: null,
  questoes: [],
  indiceQuestao: 0,
  alternativaSelecionada: null,
  respostaEnviada: false,
  modoMapa: false,
  modoRevisao: false,
  questoesRespondidas: new Set(),
  questoesCorretas: 0,
  acertosSeguidos: 0,
  pontosDuranteDesafio: 0,
  pontosAntesDoDesafio: 0,
  inicioQuestao: 0,
  heartbeat: null,
  toastTimeout: null,
  configuracaoBase: null,
};

const elemento = (id) => document.getElementById(id);

async function api(caminho, opcoes = {}) {
  const configuracao = {
    method: opcoes.method || 'GET',
    credentials: 'same-origin',
    headers: { ...(opcoes.body ? { 'Content-Type': 'application/json' } : {}), ...(opcoes.headers || {}) },
    ...(opcoes.body ? { body: JSON.stringify(opcoes.body) } : {}),
  };
  const resposta = await fetch(`${API_URL}${caminho}`, configuracao);
  let dados = {};
  try { dados = await resposta.json(); } catch (_) { dados = {}; }
  if (!resposta.ok) {
    const erro = new Error(dados.erro || `Não foi possível concluir a solicitação (${resposta.status}).`);
    erro.status = resposta.status;
    erro.payload = dados;
    throw erro;
  }
  return dados;
}

function mostrarAviso(mensagem, tipo = 'success', destino = 'auth-message') {
  const alvo = elemento(destino);
  if (!alvo) return;
  alvo.textContent = mensagem;
  alvo.className = `notice ${tipo}`;
  alvo.hidden = false;
}

function mostrarToast(mensagem) {
  const toast = elemento('toast');
  toast.textContent = mensagem;
  toast.hidden = false;
  clearTimeout(state.toastTimeout);
  state.toastTimeout = setTimeout(() => { toast.hidden = true; }, 4400);
}

function trocarModoAutenticacao(modo) {
  const login = modo === 'login';
  document.querySelectorAll('[data-auth-mode]').forEach((botao) => {
    const ativo = botao.dataset.authMode === modo;
    botao.classList.toggle('active', ativo);
    botao.setAttribute('aria-selected', String(ativo));
  });
  elemento('login-form').hidden = !login;
  elemento('register-form').hidden = login;
  elemento('auth-title').textContent = login ? 'Bom ter você de volta.' : 'Sua jornada começa aqui.';
  elemento('auth-subtitle').textContent = login ? 'Entre para continuar sua jornada.' : 'Crie sua conta e comece a avançar por fases.';
  elemento('auth-message').hidden = true;
}

document.querySelectorAll('[data-auth-mode]').forEach((botao) => {
  botao.addEventListener('click', () => trocarModoAutenticacao(botao.dataset.authMode));
});

// Os modos de login e cadastro são exclusivos; somente o formulário ativo fica no layout.
trocarModoAutenticacao('login');

elemento('login-form').addEventListener('submit', async (evento) => {
  evento.preventDefault();
  const botao = evento.currentTarget.querySelector('button[type="submit"]');
  const textoOriginal = botao.innerHTML;
  botao.disabled = true;
  botao.textContent = 'Entrando…';
  const dadosFormulario = Object.fromEntries(new FormData(evento.currentTarget));
  try {
    const dados = await api('/api/auth/login', { method: 'POST', body: dadosFormulario });
    await iniciarPlataforma(dados);
  } catch (erro) {
    mostrarAviso(erro.message, 'error');
  } finally {
    botao.disabled = false;
    botao.innerHTML = textoOriginal;
  }
});

elemento('register-form').addEventListener('submit', async (evento) => {
  evento.preventDefault();
  const botao = evento.currentTarget.querySelector('button[type="submit"]');
  const textoOriginal = botao.innerHTML;
  botao.disabled = true;
  botao.textContent = 'Criando conta…';
  const dadosFormulario = Object.fromEntries(new FormData(evento.currentTarget));
  if (!dadosFormulario.data_nascimento) delete dadosFormulario.data_nascimento;
  try {
    const dados = await api('/api/auth/register', { method: 'POST', body: dadosFormulario });
    await iniciarPlataforma({ aluno: dados.aluno });
  } catch (erro) {
    const emailEnviado = String(dadosFormulario.email || '').trim();
    if (erro.status === 409 && /e-mail/i.test(erro.message)) {
      trocarModoAutenticacao('login');
      elemento('login-form').elements.email.value = emailEnviado;
      mostrarAviso('Este e-mail já possui uma conta. Entre com sua senha para continuar e manter seu progresso.', 'error');
    } else {
      mostrarAviso(erro.message, 'error');
    }
  } finally {
    botao.disabled = false;
    botao.innerHTML = textoOriginal;
  }
});

async function iniciarPlataforma(dados) {
  state.aluno = dados.aluno;
  state.progresso = dados.progresso || null;
  elemento('auth-screen').hidden = true;
  elemento('app-layout').hidden = false;
  atualizarIdentidade();
  try {
    const [catalogo, perfil] = await Promise.all([
      api('/api/learning/catalog'),
      api('/api/learning/me'),
    ]);
    state.catalogo = catalogo.materias || [];
    state.aluno = perfil.aluno;
    state.progresso = perfil.progresso;
    montarSelectMaterias();
    atualizarPainelPerfil();
    await atualizarPainel();
    await atualizarBotoesDesafio();
    iniciarContagemDeTempo();
  } catch (erro) {
    if (erro.status === 401) mostrarTelaAutenticacao();
    else mostrarToast(erro.message);
  }
}

function mostrarTelaAutenticacao() {
  pararContagemDeTempo();
  elemento('app-layout').hidden = true;
  elemento('auth-screen').hidden = false;
  elemento('app-layout').hidden = true;
  elemento('quiz-overlay').hidden = true;
  elemento('challenge-map-screen').hidden = true;
  document.body.classList.remove('map-open');
}

async function restaurarSessao() {
  try {
    const dados = await api('/api/learning/me');
    await iniciarPlataforma(dados);
  } catch (erro) {
    if (erro.status !== 401) console.warn('Sessão inicial indisponível:', erro.message);
    mostrarTelaAutenticacao();
  }
}

function atualizarIdentidade() {
  if (!state.aluno) return;
  const nick = state.aluno.nick || state.aluno.nome || 'Estudante';
  const inicial = nick.trim().charAt(0).toUpperCase() || 'E';
  elemento('sidebar-nick').textContent = nick;
  elemento('sidebar-email').textContent = state.aluno.email || 'Minha conta';
  elemento('sidebar-avatar').textContent = inicial;
  elemento('top-avatar').textContent = inicial;
  elemento('top-points').textContent = formatarNumero(state.aluno.pontos || 0);
  elemento('stat-points').textContent = formatarNumero(state.aluno.pontos || 0);
  elemento('top-streak').textContent = state.aluno.sequencia_atual || state.aluno.foguinho || 0;
  elemento('stat-streak').textContent = state.aluno.sequencia_atual || state.aluno.foguinho || 0;
  elemento('sidebar-streak').textContent = `${state.aluno.sequencia_atual || state.aluno.foguinho || 0} ${(state.aluno.sequencia_atual || state.aluno.foguinho || 0) === 1 ? 'dia' : 'dias'}`;
  elemento('stat-minutes').textContent = formatarNumero(state.aluno.minutos_ativos || 0);
  atualizarSequenciaSemanal();
  elemento('profile-nick').value = nick;
  atualizarIdentidadeRanking();
}

function atualizarSequenciaSemanal() {
  const sequencia = Number(state.aluno?.sequencia_atual || state.aluno?.foguinho || 0);
  const bolinhas = elemento('week-dots');
  if (bolinhas) {
    Array.from(bolinhas.children).forEach((bolinha, indice) => {
      bolinha.classList.toggle('active', indice >= 7 - Math.min(sequencia, 7));
    });
  }
  const mensagem = elemento('sequence-message');
  if (mensagem) {
    mensagem.textContent = sequencia > 0
      ? `${sequencia} ${sequencia === 1 ? 'dia seguido' : 'dias seguidos'} estudando. Continue para manter seu foguinho aceso.`
      : 'Acesse diariamente para manter seu foguinho aceso.';
  }
}

function atualizarIdentidadeRanking() {
  if (!state.aluno) return;
  const nick = state.aluno.nick || state.aluno.nome || 'Estudante';
  const inicial = nick.trim().charAt(0).toUpperCase() || 'E';
  elemento('sidebar-avatar').textContent = inicial;
  elemento('top-avatar').textContent = inicial;
}

function atualizarPainelPerfil() {
  if (!state.progresso) return;
  elemento('progress-completed').textContent = formatarNumero(state.progresso.desafios_concluidos || 0);
  if (elemento('stat-lessons')) elemento('stat-lessons').textContent = formatarNumero(state.progresso.desafios_concluidos || 0);
  elemento('progress-accuracy').textContent = formatarNumero(state.progresso.precisao || 0);
  elemento('progress-answered').textContent = formatarNumero(state.progresso.questoes_respondidas || 0);
  elemento('stat-minutes').textContent = formatarNumero(state.progresso.minutos_ativos || state.aluno.minutos_ativos || 0);
  atualizarSequenciaSemanal();
}

function montarSelectMaterias() {
  const select = elemento('subject-select');
  const materiaAnterior = select.value;
  select.replaceChildren();
  state.catalogo.forEach((materia) => {
    const option = document.createElement('option');
    option.value = materia.nome;
    option.textContent = materia.nome;
    select.appendChild(option);
  });
  if (!state.catalogo.length) {
    select.add(new Option('Nenhuma matéria cadastrada', ''));
    select.disabled = true;
    return;
  }
  select.disabled = false;
  if (state.catalogo.some((materia) => materia.nome === materiaAnterior)) select.value = materiaAnterior;
  atualizarSelectTemas();
}

function atualizarSelectTemas() {
  const materia = state.catalogo.find((item) => item.nome === elemento('subject-select').value) || state.catalogo[0];
  const select = elemento('theme-select');
  select.replaceChildren();
  if (!materia || !materia.temas.length) {
    select.add(new Option('Nenhum tema cadastrado', ''));
    return;
  }
  materia.temas.forEach((tema) => select.add(new Option(tema.nome, String(tema.id_tema))));
  atualizarMapaSelecionado();
}

elemento('subject-select').addEventListener('change', atualizarSelectTemas);
elemento('theme-select').addEventListener('change', atualizarMapaSelecionado);
document.querySelectorAll('input[name="quantidade"], input[name="dificuldade"]').forEach((input) => input.addEventListener('change', atualizarPreviewPontos));
atualizarPreviewPontos();

function temaSelecionado() {
  const id = Number(elemento('theme-select').value);
  for (const materia of state.catalogo) {
    const tema = materia.temas.find((item) => item.id_tema === id);
    if (tema) return { ...tema, materia: materia.nome };
  }
  return null;
}

function fasesPorQuantidade(quantidade) {
  const mapa = { 5: 5, 10: 4, 15: 3, 20: 2 };
  return mapa[Number(quantidade)] || 5;
}

function atualizarMapaSelecionado() {
  const tema = temaSelecionado();
  const materia = elemento('subject-select').value;
  elemento('path-theme-title').textContent = tema ? tema.nome : 'Escolha um tema';
  elemento('path-subject-label').textContent = tema ? materia : 'Seu caminho será montado aqui';
  const selecionadoId = tema ? tema.id_tema : null;
  const historico = (window.__historicoDesafios || []).filter((item) => !item.modo_revisao && !String(item.nome || "").startsWith("[REFAZER] "));
  const concluidos = historico.filter((item) => item.concluido && item.tema === (tema && tema.nome) && item.materia === materia).length;
  const nivel = concluidos + 1;
  elemento('path-level').textContent = `NÍVEL ${String(nivel).padStart(2, '0')}`;
  const mapa = elemento('learning-map');
  const materiaVisual = String(materia || '').toLocaleLowerCase('pt-BR');
  const familiaVisual = materiaVisual.includes('matem') ? 0 : materiaVisual.includes('ciên') || materiaVisual.includes('biolog') ? 1 : materiaVisual.includes('hist') || materiaVisual.includes('geo') ? 2 : 3;
  const variacao = ((familiaVisual + (selecionadoId || 1) + nivel - 1) % 3);
  mapa.classList.remove('map-variant-0', 'map-variant-1', 'map-variant-2');
  mapa.classList.add(`map-variant-${variacao}`);
  const paletas = [
    ['#8b7cf6', '#c7bfff', '#f0edff'], ['#20b99a', '#91e2d1', '#e4fbf5'],
    ['#e5a33d', '#f4d18c', '#fff5df'], ['#4c9ee8', '#a9d4ff', '#e9f4ff'],
    ['#e879a9', '#f5b8d2', '#fff0f6'], ['#8aaf4f', '#cde4a5', '#f2f9e5']
  ];
  const paleta = paletas[(Math.abs(Number(selecionadoId || 0) * 3 + nivel + familiaVisual) % paletas.length)];
  mapa.style.setProperty('--map-accent', paleta[0]);
  mapa.style.setProperty('--map-accent-soft', paleta[1]);
  mapa.style.setProperty('--map-surface', paleta[2]);
  elemento('path-panel').style.setProperty('--map-accent', paleta[0]);
  elemento('path-panel').style.setProperty('--map-accent-soft', paleta[1]);
  const layouts = [
    [{ x: '5%', y: '66%' }, { x: '32%', y: '38%' }, { x: '61%', y: '64%' }, { x: '94%', y: '27%' }],
    [{ x: '5%', y: '32%' }, { x: '32%', y: '68%' }, { x: '61%', y: '35%' }, { x: '94%', y: '62%' }],
    [{ x: '5%', y: '64%' }, { x: '32%', y: '35%' }, { x: '61%', y: '66%' }, { x: '94%', y: '30%' }],
  ];
  const caminhos = [
    'M25 145 C75 145 75 70 145 90 S220 165 285 105 S365 45 425 95 S500 145 575 55',
    'M25 70 C90 45 90 160 180 145 S245 45 330 75 S440 155 575 130',
    'M25 140 C90 170 100 50 180 75 S260 160 345 130 S455 35 575 65',
  ];
  const pontosMapa = layouts[variacao];
  const nos = document.querySelectorAll('.map-node');
  nos.forEach((no, indice) => {
    no.style.setProperty('--x', pontosMapa[indice].x);
    no.style.setProperty('--y', pontosMapa[indice].y);
    no.classList.remove('map-node-done', 'map-node-current', 'map-node-locked');
    if (indice < Math.min(concluidos, 3)) no.classList.add('map-node-done');
    else if (indice === Math.min(concluidos, 3)) no.classList.add('map-node-current');
    else no.classList.add('map-node-locked');
    const span = no.querySelector('span');
    if (span) span.textContent = no.classList.contains('map-node-done') ? '✓' : String(indice + 1);
  });
  const linhaMapa = mapa.querySelector('.map-path-line path');
  if (linhaMapa) linhaMapa.setAttribute('d', caminhos[variacao]);
  const meta = mapa.querySelector('.map-goal');
  if (meta) { meta.style.left = layouts[variacao][3].x; meta.style.top = layouts[variacao][3].y; }
  if (selecionadoId && tema) {
    const mapLabel = document.querySelector('.map-node-current small');
    if (mapLabel) mapLabel.textContent = `Fase ${nivel}`;
  }
  atualizarPreviewPontos();
  const quantidade = Number(document.querySelector('input[name="quantidade"]:checked')?.value || 5);
  const numeroFases = fasesPorQuantidade(quantidade);
  if (elemento('path-journey-count')) {
    elemento('path-journey-count').textContent = tema
      ? `Sua jornada de ${numeroFases} desafios começa com ${tema.nome}. Cada fase concluída muda o mapa.`
      : 'Escolha uma matéria e um tema para preparar sua jornada.';
  }
}

function atualizarPreviewPontos() {
  const quantidade = Number(document.querySelector('input[name="quantidade"]:checked')?.value || 5);
  const dificuldade = document.querySelector('input[name="dificuldade"]:checked')?.value || 'normal';
  const pontosPorQuestao = dificuldade === 'facil' ? 10 : dificuldade === 'dificil' ? 20 : 15;
  const fases = fasesPorQuantidade(quantidade);
  if (elemento('possible-points')) elemento('possible-points').textContent = `Até ${formatarNumero(quantidade * pontosPorQuestao)} pontos por fase`;
  if (elemento('journey-count')) elemento('journey-count').textContent = `${fases} ${fases === 1 ? 'desafio' : 'desafios'}`;
  if (elemento('journey-description')) elemento('journey-description').textContent = `${quantidade} questões por fase · ${quantidade * fases} questões na jornada`;
  if (elemento('journey-steps')) {
    const passos = elemento('journey-steps');
    passos.replaceChildren();
    for (let indice = 0; indice < fases; indice += 1) {
      const passo = document.createElement('i');
      if (indice === 0) passo.classList.add('is-current');
      passos.appendChild(passo);
    }
    passos.setAttribute('aria-label', `${fases} desafios planejados`);
  }
  if (elemento('path-journey-count')) {
    const tema = temaSelecionado();
    elemento('path-journey-count').textContent = tema
      ? `Jornada planejada: ${fases} desafios de ${quantidade} questões cada.`
      : `Você terá ${fases} desafios, com ${quantidade} questões em cada fase.`;
  }
}

function dificuldadeDaFase(dificuldadeBase, fase) {
  // A progressão é gradual e limitada a um único nível acima do escolhido.
  if (dificuldadeBase === 'facil' && fase >= 5) return 'normal';
  if (dificuldadeBase === 'normal' && fase >= 7) return 'dificil';
  return dificuldadeBase;
}

function fasesConcluidasDoTema(idTema) {
  return (window.__historicoDesafios || []).filter((item) => item.concluido && Number(item.id_tema) === Number(idTema)).length;
}

async function criarProximoDesafio({ idTema, quantidade, dificuldadeBase, mostrarMapa = true, fasesPlanejadas = fasesPorQuantidade(quantidade), faseNaJornada = 1 }) {
  const fase = fasesConcluidasDoTema(idTema) + 1;
  const dificuldade = dificuldadeDaFase(dificuldadeBase, fase);
  const dados = await api('/api/learning/challenges', { method: 'POST', body: {
    id_tema: Number(idTema), quantidade_questoes: Number(quantidade), dificuldade,
  }});
  state.desafio = dados.desafio;
  state.temaAtual = dados.tema;
  state.questoes = dados.questoes || [];
  state.indiceQuestao = 0;
  state.alternativaSelecionada = null;
  state.respostaEnviada = false;
  state.modoMapa = mostrarMapa;
  state.modoRevisao = false;
  state.questoesRespondidas = new Set();
  state.questoesCorretas = 0;
  state.acertosSeguidos = 0;
  state.pontosDuranteDesafio = 0;
  state.pontosAntesDoDesafio = Number(state.aluno?.pontos || 0);
  state.configuracaoBase = { idTema: Number(idTema), quantidade: Number(quantidade), dificuldadeBase, fasesPlanejadas: Number(fasesPlanejadas), faseNaJornada: Number(faseNaJornada) };
  if (dificuldade !== dificuldadeBase) {
    mostrarToast(`Nova fase desbloqueada! A dificuldade subiu um pouco para ${dificuldade === 'normal' ? 'Normal' : 'Difícil'}.`);
  } else {
    mostrarToast(`Fase ${dados.desafio.nivel_mapa || fase} pronta. Bora continuar?`);
  }
  if (mostrarMapa) abrirMapaDesafio(); else abrirQuiz();
}

async function atualizarBotoesDesafio() {
  const continuarTopo = elemento('jump-to-challenge');
  const refazer = elemento('replay-latest-button');
  try {
    const [ativo, historico] = await Promise.all([
      api('/api/learning/active-challenge'),
      api('/api/learning/history')
    ]);
    window.__historicoDesafios = historico.historico || [];
    const concluido = window.__historicoDesafios.find((item) => item.concluido && item.id_tema && !item.modo_revisao && !String(item.nome || "").startsWith("[REFAZER] "));
    refazer.hidden = !concluido;
    if (concluido) refazer.dataset.historyId = String(concluido.id_desafio);
    continuarTopo.hidden = !ativo.ativo;
    continuarTopo.dataset.challengeId = ativo.ativo ? String(ativo.desafio.id_desafio) : '';
    continuarTopo.innerHTML = ativo.ativo
      ? '<span aria-hidden="true">▶</span> <span>Continuar desafio</span> <span aria-hidden="true">→</span>'
      : '';
    elemento('create-challenge-button').innerHTML = ativo.ativo
      ? '<span aria-hidden="true">✦</span> Criar um novo desafio <span aria-hidden="true">→</span>'
      : '<span aria-hidden="true">✦</span> Gerar desafio <span aria-hidden="true">→</span>';
  } catch (erro) { console.warn('Não foi possível atualizar as ações de desafio:', erro.message); }
}

async function continuarDesafioSalvo(idInformado = null) {
  try {
    const id = idInformado || elemento('jump-to-challenge').dataset.challengeId;
    const dados = await api(`/api/learning/challenges/${id}`);
    state.desafio = dados.desafio;
    state.temaAtual = state.catalogo.flatMap((m) => m.temas || []).find((t) => Number(t.id_tema) === Number(dados.desafio.id_tema)) || { nome: dados.desafio.nome, materia: '' };
    state.questoes = dados.questoes || [];
    state.indiceQuestao = 0;
    state.alternativaSelecionada = null;
    state.respostaEnviada = false;
    state.modoMapa = true;
    state.questoesRespondidas = new Set();
    state.questoesCorretas = 0;
    state.acertosSeguidos = 0;
    state.pontosDuranteDesafio = 0;
    state.pontosAntesDoDesafio = Number(state.aluno?.pontos || 0);
    const respondidas = dados.respondidas || {};
    state.questoes.forEach((q, i) => { if (respondidas[String(q.id_questao)] || respondidas[q.id_questao]) state.questoesRespondidas.add(i); });
    const cfg = document.querySelector('input[name="quantidade"]:checked');
    state.configuracaoBase = { idTema: Number(dados.desafio.id_tema), quantidade: Number(dados.desafio.quantidade_questoes || state.questoes.length), dificuldadeBase: 'normal', fasesPlanejadas: fasesPorQuantidade(Number(dados.desafio.quantidade_questoes || state.questoes.length)), faseNaJornada: 1 };
    abrirMapaDesafio();
    mostrarToast('Desafio restaurado. Continue de onde você parou.');
  } catch (erro) { mostrarToast(`Não foi possível continuar: ${erro.message}`); }
}

elemento('jump-to-challenge').addEventListener('click', (evento) => {
  if (evento.currentTarget.dataset.challengeId) continuarDesafioSalvo(evento.currentTarget.dataset.challengeId);
});
elemento('replay-latest-button').addEventListener('click', async () => {
  const item = (window.__historicoDesafios || []).find((registro) => String(registro.id_desafio) === elemento('replay-latest-button').dataset.historyId && !registro.modo_revisao && !String(registro.nome || "").startsWith("[REFAZER] "));
  if (item) await refazerDesafio(item);
});

elemento('challenge-form').addEventListener('submit', async (evento) => {
  evento.preventDefault();
  const tema = temaSelecionado();
  if (!tema) {
    mostrarToast('Selecione uma matéria e um tema antes de gerar o desafio.');
    return;
  }
  const botao = elemento('create-challenge-button');
  const textoOriginal = botao.innerHTML;
  botao.disabled = true;
  botao.innerHTML = '<span class="button-spark">✦</span> Preparando questões…';
  try {
    const quantidade = Number(document.querySelector('input[name="quantidade"]:checked').value);
    const dificuldadeBase = document.querySelector('input[name="dificuldade"]:checked').value;
    const fase = fasesConcluidasDoTema(tema.id_tema) + 1;
    const dificuldade = dificuldadeDaFase(dificuldadeBase, fase);
    const dados = await api('/api/learning/challenges', {
      method: 'POST',
      body: { id_tema: tema.id_tema, quantidade_questoes: quantidade, dificuldade },
    });
    state.configuracaoBase = { idTema: Number(tema.id_tema), quantidade, dificuldadeBase, fasesPlanejadas: fasesPorQuantidade(quantidade), faseNaJornada: 1 };
    state.desafio = dados.desafio;
    state.temaAtual = dados.tema;
    state.questoes = dados.questoes || [];
    state.indiceQuestao = 0;
    state.alternativaSelecionada = null;
    state.respostaEnviada = false;
    state.modoMapa = true;
    state.questoesRespondidas = new Set();
    state.questoesCorretas = 0;
    state.pontosDuranteDesafio = 0;
    state.acertosSeguidos = 0;
    state.pontosAntesDoDesafio = Number(state.aluno.pontos || 0);
    if (dados.origem_questoes !== 'ia') {
      mostrarToast('Mapa criado com questões demonstrativas locais. Para gerar questões novas com IA, configure OPENAI_API_KEY no servidor.');
    } else {
      mostrarToast('Seu mapa de desafio foi criado pela IA. Clique em uma bolinha para começar.');
    }
    abrirMapaDesafio();
    await atualizarBotoesDesafio();
  } catch (erro) {
    mostrarToast(erro.message);
  } finally {
    botao.disabled = false;
    botao.innerHTML = textoOriginal;
  }
});

function abrirMapaDesafio() {
  if (!state.questoes.length) {
    mostrarToast('O desafio foi criado sem questões disponíveis. Tente novamente.');
    return;
  }
  elemento('quiz-overlay').hidden = true;
  elemento('challenge-map-screen').hidden = false;
  document.body.classList.add('map-open');
  renderizarMapaDesafio();
  elemento('space-map-scroll').scrollTop = 0;
  window.scrollTo({ top: 0, behavior: 'auto' });
}

function renderizarMapaDesafio() {
  if (!state.desafio || !state.temaAtual || !state.questoes.length) return;
  const quantidade = state.questoes.length;
  const nivel = state.desafio.nivel_mapa || 1;
  elemento('challenge-map-title').textContent = state.temaAtual.nome;
  const jornada = state.configuracaoBase;
  const faseJornada = jornada?.faseNaJornada || 1;
  const totalFases = jornada?.fasesPlanejadas || fasesPorQuantidade(quantidade);
  elemento('challenge-map-subtitle').textContent = `${state.temaAtual.materia} · Fase ${nivel} · Jornada ${faseJornada}/${totalFases} — selecione uma bolinha`; 
  elemento('map-progress-count').textContent = `${state.questoesRespondidas.size}/${quantidade}`;
  elemento('map-xp-total').textContent = `${formatarNumero(state.aluno?.pontos || 0)} XP`;

  const moldura = elemento('space-map');
  const nomeMateriaMapa = String(state.temaAtual.materia || '').toLocaleLowerCase('pt-BR');
  const familiaMapa = nomeMateriaMapa.includes('matem') ? 0 : nomeMateriaMapa.includes('ciên') || nomeMateriaMapa.includes('biolog') ? 1 : nomeMateriaMapa.includes('hist') || nomeMateriaMapa.includes('geo') ? 2 : 3;
  const temaVisual = ((familiaMapa + Number(state.temaAtual.id_tema || 1) + Number(nivel) - 1) % 4) + 1;
  moldura.classList.remove('map-world-1', 'map-world-2', 'map-world-3', 'map-world-4', 'map-subject-math', 'map-subject-science', 'map-subject-history', 'map-subject-geography', 'map-subject-language', 'map-subject-default');
  moldura.classList.add(`map-world-${temaVisual}`);
  const textoTema = `${state.temaAtual.materia || ''} ${state.temaAtual.nome || ''}`.toLocaleLowerCase('pt-BR');
  const familiaClasse = /matem|álgebra|geometr|cálculo/.test(textoTema) ? 'math' : /ciên|biolog|quím|físic|natureza/.test(textoTema) ? 'science' : /hist|antig|medieval|civiliza/.test(textoTema) ? 'history' : /geograf|clima|relevo|mapa/.test(textoTema) ? 'geography' : /portugu|literat|inglês|língua|gramát/.test(textoTema) ? 'language' : 'default';
  moldura.classList.add(`map-subject-${familiaClasse}`);
  const largura = Math.max(1400, quantidade * 145);
  const altura = 560;
  moldura.style.setProperty('--map-width', `${largura}px`);
  moldura.style.setProperty('--map-height', `${altura}px`);
  const rotaSvg = elemento('space-map-route');
  rotaSvg.setAttribute('viewBox', `0 0 ${largura} ${altura}`);
  const containerNos = elemento('challenge-node-list');
  const grupoLinhas = elemento('space-map-route-paths');
  containerNos.replaceChildren();
  grupoLinhas.replaceChildren();

  const pontos = state.questoes.map((_, indice) => {
    const progresso = quantidade === 1 ? 0.5 : indice / (quantidade - 1);
    return { x: largura * (0.035 + progresso * 0.93), y: altura * (0.50 + Math.sin(indice * 1.42) * 0.27 + Math.cos(indice * 0.61) * 0.08) };
  });

  pontos.slice(0, -1).forEach((ponto, indice) => {
    const destino = pontos[indice + 1];
    const meioX = (ponto.x + destino.x) / 2;
    const inclinacao = indice % 2 === 0 ? -58 : 58;
    const caminho = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    caminho.setAttribute('d', `M ${ponto.x.toFixed(1)} ${ponto.y.toFixed(1)} Q ${meioX.toFixed(1)} ${( ((ponto.y + destino.y) / 2) + inclinacao ).toFixed(1)} ${destino.x.toFixed(1)} ${destino.y.toFixed(1)}`);
    caminho.setAttribute('class', indice % 2 === 0 ? 'route-lime' : 'route-turquoise');
    grupoLinhas.appendChild(caminho);
  });

  state.questoes.forEach((questao, indice) => {
    const respondida = state.questoesRespondidas.has(indice);
    const botao = document.createElement('button');
    botao.type = 'button';
    botao.className = `challenge-map-node ${indice % 2 === 0 ? 'node-lime' : 'node-turquoise'}${respondida ? ' node-complete' : ''}`;
    botao.style.left = `${(pontos[indice].x / largura) * 100}%`;
    botao.style.top = `${(pontos[indice].y / altura) * 100}%`;
    botao.setAttribute('aria-label', `Questão ${indice + 1}${respondida ? ', concluída' : ''}`);
    botao.title = `Questão ${indice + 1}${respondida ? ' — concluída' : ''}`;
    botao.innerHTML = `<span class="node-play-mark" aria-hidden="true">${respondida ? '✓' : '▶'}</span><span class="node-caption">Questão ${indice + 1}</span>`;
    botao.addEventListener('click', () => {
      if (respondida) {
        mostrarToast('Esta questão já foi concluída. Escolha outra bolinha para continuar.');
        return;
      }
      state.indiceQuestao = indice;
      abrirQuestaoDoMapa();
    });
    containerNos.appendChild(botao);
  });
}

function abrirQuestaoDoMapa() {
  if (!state.questoes[state.indiceQuestao]) return;
  elemento('quiz-overlay').hidden = false;
  elemento('quiz-content').hidden = false;
  elemento('quiz-result').hidden = true;
  elemento('quiz-theme-label').textContent = `${state.temaAtual.materia} · ${state.temaAtual.nome}`;
  elemento('quiz-xp-total').textContent = formatarNumero(state.aluno.pontos || 0);
  mostrarQuestaoAtual();
}

function fecharMapaDesafio() {
  elemento('quiz-overlay').hidden = true;
  elemento('challenge-map-screen').hidden = true;
  document.body.classList.remove('map-open');
  trocarVisao('study');
  atualizarPainel().catch((erro) => console.warn('Não foi possível atualizar o painel:', erro.message));
}

elemento('exit-challenge-map').addEventListener('click', fecharMapaDesafio);
elemento('map-close-bottom').addEventListener('click', fecharMapaDesafio);

elemento('theme-toggle').addEventListener('click', () => {
  document.body.classList.toggle('theme-dark');
  const escuro = document.body.classList.contains('theme-dark');
  elemento('theme-toggle').textContent = escuro ? '☼' : '◐';
  elemento('theme-toggle').title = escuro ? 'Usar tema claro' : 'Usar tema escuro';
  try { localStorage.setItem('explainer-theme-v3', escuro ? 'dark' : 'light'); } catch (_) {}
});
try {
  if (localStorage.getItem('explainer-theme-v3') === 'dark') {
    document.body.classList.add('theme-dark');
    elemento('theme-toggle').textContent = '☼';
    elemento('theme-toggle').title = 'Usar tema claro';
  }
} catch (_) {}

function abrirQuiz() {
  if (!state.questoes.length) {
    mostrarToast('O desafio foi criado sem questões disponíveis. Tente novamente.');
    return;
  }
  elemento('quiz-overlay').hidden = false;
  elemento('quiz-content').hidden = false;
  elemento('quiz-result').hidden = true;
  elemento('quiz-theme-label').textContent = `${state.temaAtual.materia} · ${state.temaAtual.nome}`;
  elemento('quiz-xp-total').textContent = formatarNumero(state.aluno.pontos || 0);
  mostrarQuestaoAtual();
}

function mostrarQuestaoAtual() {
  const questao = state.questoes[state.indiceQuestao];
  state.alternativaSelecionada = null;
  state.respostaEnviada = false;
  state.inicioQuestao = Date.now();
  elemento('quiz-counter').textContent = `Questão ${state.indiceQuestao + 1} de ${state.questoes.length}`;
  elemento('quiz-question-number').textContent = `Questão ${state.indiceQuestao + 1}`;
  elemento('quiz-progress-fill').style.width = `${(state.indiceQuestao / state.questoes.length) * 100}%`;
  elemento('quiz-question-title').textContent = questao.enunciado;
  elemento('quiz-action-hint').textContent = 'Escolha uma alternativa';
  elemento('next-question').disabled = true;
  elemento('next-question').innerHTML = state.modoMapa ? 'Continuar' : 'Confirmar resposta <span>→</span>';
  elemento('answer-feedback').hidden = true;
  elemento('answer-feedback').classList.remove('wrong');
  const lista = elemento('answer-list');
  lista.replaceChildren();
  LETRAS.forEach((letra) => {
    const botao = document.createElement('button');
    botao.type = 'button';
    botao.className = 'answer-option';
    botao.dataset.answer = letra;
    const marcador = document.createElement('span');
    marcador.className = 'answer-letter';
    marcador.textContent = letra;
    const texto = document.createElement('span');
    texto.className = 'answer-text';
    texto.textContent = questao.alternativas[letra] || 'Alternativa indisponível';
    botao.append(marcador, texto);
    botao.addEventListener('click', () => selecionarAlternativa(letra));
    lista.appendChild(botao);
  });
}

function selecionarAlternativa(letra) {
  if (state.respostaEnviada) return;
  state.alternativaSelecionada = letra;
  document.querySelectorAll('.answer-option').forEach((botao) => {
    botao.classList.toggle('selected', botao.dataset.answer === letra);
  });
  elemento('next-question').disabled = false;
  elemento('quiz-action-hint').textContent = `Alternativa ${letra} selecionada`;
}

elemento('next-question').addEventListener('click', async () => {
  if (state.respostaEnviada) {
    if (state.modoMapa) {
      if (state.questoesRespondidas.size >= state.questoes.length) {
        await concluirQuiz();
      } else {
        elemento('quiz-overlay').hidden = true;
        renderizarMapaDesafio();
        mostrarToast('Questão concluída. Escolha a próxima bolinha no mapa.');
      }
      return;
    }
    if (state.indiceQuestao < state.questoes.length - 1) {
      state.indiceQuestao += 1;
      mostrarQuestaoAtual();
    } else {
      await concluirQuiz();
    }
    return;
  }
  if (!state.alternativaSelecionada) return;
  const botaoProximo = elemento('next-question');
  botaoProximo.disabled = true;
  botaoProximo.textContent = 'Verificando…';
  const questao = state.questoes[state.indiceQuestao];
  const segundosGastos = Math.max(0, Math.round((Date.now() - state.inicioQuestao) / 1000));
  try {
    const resultado = await api(`/api/learning/challenges/${state.desafio.id_desafio}/answer`, {
      method: 'POST',
      body: { id_questao: questao.id_questao, alternativa: state.alternativaSelecionada, segundos_gastos: segundosGastos },
    });
    state.respostaEnviada = true;
    state.pontosDuranteDesafio += resultado.pontos_ganhos || 0;
    if (resultado.correta) state.questoesCorretas += 1;
    if (state.modoMapa) state.questoesRespondidas.add(state.indiceQuestao);
    state.aluno.pontos = resultado.pontos_totais;
    state.aluno.minutos_ativos = Math.max(state.aluno.minutos_ativos || 0, resultado.minutos_ativos || 0);
    elemento('quiz-xp-total').textContent = formatarNumero(state.aluno.pontos || 0);
    atualizarIdentidade();
    document.querySelectorAll('.answer-option').forEach((botao) => {
      botao.disabled = true;
      if (botao.dataset.answer === resultado.alternativa_correta) botao.classList.add('correct');
      else if (botao.dataset.answer === state.alternativaSelecionada && !resultado.correta) botao.classList.add('incorrect');
    });
    const feedback = elemento('answer-feedback');
    feedback.hidden = false;
    feedback.classList.toggle('wrong', !resultado.correta);
    elemento('feedback-title').textContent = resultado.correta ? 'Resposta correta!' : `A resposta correta é ${resultado.alternativa_correta}.`;
    elemento('feedback-text').textContent = resultado.explicacao;
    elemento('feedback-points').textContent = resultado.correta ? `+${resultado.pontos_ganhos} pontos adicionados ao seu total.` : 'Nenhum ponto nesta questão. Continue tentando.';
    if (resultado.correta) {
      state.acertosSeguidos += 1;
      const elogios = [
        'Mandou bem! Você acabou de conquistar mais um acerto.',
        'Boa leitura da questão! Seu esforço está aparecendo.',
        'Acertou! Mais um passo na sua jornada.',
        'Resposta certa! Pode comemorar essa evolução.',
        'Aí sim! Você está construindo conhecimento de verdade.'
      ];
      if (state.acertosSeguidos > 0 && state.acertosSeguidos % 5 === 0) {
        mostrarToast(`🔥 CINCO SEGUIDAS! ${state.acertosSeguidos} acertos em sequência. Você está em ótima fase!`);
      } else {
        mostrarToast(elogios[(state.acertosSeguidos - 1) % elogios.length]);
      }
    } else {
      state.acertosSeguidos = 0;
    }
    elemento('quiz-progress-fill').style.width = `${(state.questoesRespondidas.size / state.questoes.length) * 100}%`;
    elemento('quiz-action-hint').textContent = state.modoMapa
      ? (state.questoesRespondidas.size >= state.questoes.length ? 'Todas as questões foram respondidas.' : 'Volte ao mapa para escolher outra bolinha.')
      : (resultado.correta ? 'Boa! Vamos continuar.' : 'Revise a explicação e siga para a próxima.');
    botaoProximo.disabled = false;
    botaoProximo.innerHTML = state.modoMapa
      ? (state.questoesRespondidas.size >= state.questoes.length ? 'Concluir fase →' : 'Voltar ao mapa')
      : (state.indiceQuestao < state.questoes.length - 1 ? 'Próxima questão <span>→</span>' : 'Ver resultado <span>→</span>');
    if (state.modoMapa) renderizarMapaDesafio();
  } catch (erro) {
    mostrarToast(erro.message);
    botaoProximo.disabled = false;
    botaoProximo.innerHTML = 'Tentar novamente <span>→</span>';
  }
});

async function concluirQuiz() {
  const botao = elemento('next-question');
  botao.disabled = true;
  botao.textContent = 'Salvando resultado…';
  try {
    const resultado = await api(`/api/learning/challenges/${state.desafio.id_desafio}/complete`, { method: 'POST', body: {} });
    state.progresso = resultado.progresso;
    state.aluno.pontos = resultado.pontos_totais;
    elemento('quiz-content').hidden = true;
    elemento('quiz-result').hidden = false;
    elemento('result-correct').textContent = `${resultado.questoes_corretas}/${resultado.quantidade_questoes}`;
    elemento('result-points').textContent = `+${formatarNumero(resultado.pontos_ganhos)}`;
    elemento('result-accuracy').textContent = `${Math.round((resultado.questoes_corretas / Math.max(resultado.quantidade_questoes, 1)) * 100)}%`;
    elemento('result-title').textContent = resultado.questoes_corretas === resultado.quantidade_questoes ? 'Desafio perfeito!' : 'Mais uma fase concluída!';
    elemento('result-description').textContent = resultado.questoes_corretas === resultado.quantidade_questoes ? 'Você acertou todas as questões. Continue mantendo esse ritmo.' : 'Cada tentativa conta. Revise os conceitos e avance para a próxima fase.';
    elemento('result-bonus').hidden = !(resultado.bonus_perfeito > 0);
    const jornadaAtual = state.configuracaoBase?.faseNaJornada || 1;
    const totalJornada = state.configuracaoBase?.fasesPlanejadas || fasesPorQuantidade(state.questoes.length);
    elemento('next-challenge').hidden = Boolean(state.modoRevisao);
    elemento('finish-quiz').textContent = state.modoRevisao ? 'Voltar ao mapa de revisão' : 'Voltar ao mapa';
    elemento('next-challenge').innerHTML = jornadaAtual >= totalJornada
      ? 'Concluir jornada <span>✓</span>'
      : `Próxima fase ${jornadaAtual + 1}/${totalJornada} <span>→</span>`;
    elemento('quiz-progress-fill').style.width = '100%';
    atualizarIdentidade();
    atualizarPainelPerfil();
    mostrarToast(resultado.questoes_corretas === resultado.quantidade_questoes ? '🏆 Desafio perfeito! Você acertou todas e concluiu esta fase!' : '✨ Fase concluída! Seu progresso foi salvo.');
    await atualizarPainel();
    await atualizarBotoesDesafio();

  } catch (erro) {
    mostrarToast(erro.message);
    botao.disabled = false;
    botao.innerHTML = 'Tentar salvar resultado <span>→</span>';
  }
}

elemento('finish-quiz').addEventListener('click', async () => {
  elemento('quiz-overlay').hidden = true;
  if (state.modoMapa && !elemento('challenge-map-screen').hidden) {
    renderizarMapaDesafio();
  } else {
    trocarVisao('study');
  }
  await atualizarPainel();
  if (state.modoMapa && !elemento('challenge-map-screen').hidden) renderizarMapaDesafio();
});

elemento('close-quiz').addEventListener('click', () => {
  if (state.modoRevisao) { elemento('quiz-overlay').hidden = true; renderizarMapaDesafio(); return; }
  if (state.desafio && !elemento('quiz-result').hidden) {
    elemento('quiz-overlay').hidden = true;
    renderizarMapaDesafio();
    return;
  }
  const confirmou = window.confirm('Voltar ao mapa? A resposta desta questão só será salva quando você confirmar.');
  if (confirmou) {
    elemento('quiz-overlay').hidden = true;
    renderizarMapaDesafio();
  }
});

async function atualizarPainel() {
  const tarefas = await Promise.allSettled([
    api('/api/learning/me'),
    api(`/api/learning/ranking?limite=${elemento('ranking-view').hidden ? 5 : 100}`),
    api('/api/learning/history'),
  ]);
  if (tarefas[0].status === 'fulfilled') {
    state.aluno = tarefas[0].value.aluno;
    state.progresso = tarefas[0].value.progresso;
    atualizarIdentidade();
    atualizarPainelPerfil();
  }
  if (tarefas[1].status === 'fulfilled') renderizarRankingPreview(tarefas[1].value);
  if (tarefas[2].status === 'fulfilled') {
    window.__historicoDesafios = tarefas[2].value.historico || [];
    renderizarHistorico(tarefas[2].value.historico || []);
    atualizarMapaSelecionado();
  }
}

function renderizarRankingPreview(dados) {
  const contenedor = elemento('ranking-preview-list');
  contenedor.replaceChildren();
  const itens = dados.itens || [];
  if (!itens.length) {
    contenedor.innerHTML = '<div class="empty-state">Ainda não há estudantes no ranking.</div>';
    return;
  }
  itens.slice(0, 4).forEach((item) => {
    const linha = document.createElement('div');
    linha.className = 'ranking-row';
    const posicao = document.createElement('span');
    posicao.className = `ranking-place ${item.posicao === 1 ? 'first' : ''}`;
    posicao.textContent = String(item.posicao).padStart(2, '0');
    const avatar = document.createElement('span');
    avatar.className = 'ranking-avatar';
    avatar.textContent = (item.nick || 'E').charAt(0).toUpperCase();
    const nome = document.createElement('span');
    nome.className = 'ranking-name';
    nome.textContent = item.nick || 'Estudante';
    const detalhe = document.createElement('small');
    detalhe.textContent = `${item.sequencia_atual || 0} dias de sequência`;
    nome.appendChild(detalhe);
    const pontos = document.createElement('span');
    pontos.className = 'ranking-score';
    pontos.textContent = `${formatarNumero(item.pontos)} pts`;
    linha.append(posicao, avatar, nome, pontos);
    contenedor.appendChild(linha);
  });
  renderizarTabelaRanking(dados);
}

function renderizarTabelaRanking(dados) {
  const itensRanking = dados.itens || [];
  const posicaoUsuario = itensRanking.find((item) => state.aluno && item.id_aluno === state.aluno.id_aluno)?.posicao || dados.posicao_usuario;
  if (elemento('stat-rank')) elemento('stat-rank').textContent = posicaoUsuario ? `#${posicaoUsuario}` : '#—';
  const corpo = elemento('ranking-table-body');
  corpo.replaceChildren();
  const itens = dados.itens || [];
  if (!itens.length) {
    const linha = corpo.insertRow();
    linha.insertCell().colSpan = 5;
    linha.cells[0].textContent = 'Ainda não há pontuações registradas.';
    return;
  }
  itens.forEach((item) => {
    const linha = corpo.insertRow();
    if (state.aluno && item.id_aluno === state.aluno.id_aluno) linha.className = 'current-user-row';
    const rank = linha.insertCell();
    const medalha = document.createElement('span');
    const classe = item.posicao === 1 ? 'gold' : item.posicao === 2 ? 'silver' : item.posicao === 3 ? 'bronze' : '';
    medalha.className = `rank-medal ${classe}`;
    medalha.textContent = item.posicao;
    rank.appendChild(medalha);
    const estudante = linha.insertCell();
    estudante.className = 'student-cell';
    const avatar = document.createElement('span');
    avatar.className = 'ranking-avatar';
    avatar.textContent = (item.nick || 'E').charAt(0).toUpperCase();
    const nome = document.createElement('span');
    nome.textContent = item.nick || 'Estudante';
    estudante.append(avatar, nome);
    linha.insertCell().textContent = `${item.sequencia_atual || 0} dias`;
    linha.insertCell().textContent = `${formatarNumero(item.minutos_ativos || 0)} min`;
    const pontos = linha.insertCell();
    pontos.className = 'points-cell';
    pontos.textContent = `${formatarNumero(item.pontos)} pts`;
  });
}

function renderizarHistorico(historico) {
  const preview = elemento('recent-preview-list');
  preview.replaceChildren();
  const corpo = elemento('history-table-body');
  corpo.replaceChildren();
  if (!historico.length) {
    preview.innerHTML = '<div class="empty-state">Você ainda não concluiu um desafio. Seu primeiro está a um clique.</div>';
    const linha = corpo.insertRow();
    linha.insertCell().colSpan = 6;
    linha.cells[0].textContent = 'Seu histórico aparecerá aqui depois do primeiro desafio.';
    return;
  }
  historico.slice(0, 3).forEach((item) => {
    const linha = document.createElement('div');
    linha.className = 'recent-row';
    const icone = document.createElement('span');
    icone.className = 'recent-icon';
    icone.textContent = item.concluido ? '✓' : '◷';
    const copia = document.createElement('span');
    copia.className = 'recent-copy';
    const titulo = document.createElement('strong');
    titulo.textContent = item.nome;
    const subtitulo = document.createElement('span');
    subtitulo.textContent = `${item.materia} · ${item.dificuldade}`;
    copia.append(titulo, subtitulo);
    const pontos = document.createElement('span');
    pontos.className = 'recent-points';
    pontos.textContent = `+${formatarNumero(item.pontuacao_obtida || 0)}`;
    linha.append(icone, copia, pontos);
    preview.appendChild(linha);
  });
  historico.forEach((item) => {
    const linha = corpo.insertRow();
    const nome = linha.insertCell();
    nome.textContent = item.nome;
    const tema = linha.insertCell();
    tema.textContent = `${item.materia} · ${item.tema}`;
    const dificuldade = linha.insertCell();
    const tag = document.createElement('span');
    tag.className = `difficulty-tag ${item.dificuldade === 'Difícil' ? 'hard' : item.dificuldade === 'Normal' ? 'normal' : ''}`;
    tag.textContent = item.dificuldade;
    dificuldade.appendChild(tag);
    linha.insertCell().textContent = `${formatarNumero(item.pontuacao_obtida || 0)} pts`;
    linha.insertCell().textContent = formatarData(item.data_realizacao);
    const acao = linha.insertCell();
    const refazer = document.createElement('button');
    refazer.type = 'button';
    refazer.className = 'history-replay-button';
    refazer.textContent = 'Refazer ↻';
    refazer.disabled = !item.id_tema;
    refazer.title = 'Criar uma nova tentativa com a mesma matéria, tema e dificuldade';
    refazer.addEventListener('click', () => refazerDesafio(item));
    acao.appendChild(refazer);
  });
}

async function refazerDesafio(item) {
  try {
    mostrarToast('Preparando uma nova tentativa…');
    const quantidade = [5, 10, 15, 20].includes(Number(item.quantidade_questoes)) ? Number(item.quantidade_questoes) : 5;
    const dados = await api('/api/learning/challenges', { method: 'POST', body: {
      id_tema: Number(item.id_tema), quantidade_questoes: quantidade,
      dificuldade: item.dificuldade === 'Fácil' ? 'facil' : item.dificuldade === 'Difícil' ? 'dificil' : 'normal',
      refazer: true
    }});
    state.desafio = dados.desafio;
    state.temaAtual = dados.tema;
    state.questoes = dados.questoes || [];
    state.indiceQuestao = 0;
    state.alternativaSelecionada = null;
    state.respostaEnviada = false;
    state.modoMapa = true;
    state.modoRevisao = true;
    state.questoesRespondidas = new Set();
    state.questoesCorretas = 0;
    state.acertosSeguidos = 0;
    state.pontosDuranteDesafio = 0;
    state.pontosAntesDoDesafio = Number(state.aluno.pontos || 0);
    state.configuracaoBase = { idTema: Number(item.id_tema), quantidade, dificuldadeBase: item.dificuldade === 'Fácil' ? 'facil' : item.dificuldade === 'Difícil' ? 'dificil' : 'normal', fasesPlanejadas: fasesPorQuantidade(quantidade), faseNaJornada: 1 };
    abrirMapaDesafio();
    mostrarToast('Modo de revisão: você pode sair a qualquer momento. Esta tentativa não altera sua jornada nem concede pontos.');
  } catch (erro) {
    mostrarToast(`Não foi possível refazer: ${erro.message}`);
  }
}

elemento('next-challenge').addEventListener('click', async () => {
  if (state.modoRevisao) { elemento('quiz-overlay').hidden = true; renderizarMapaDesafio(); return; }
  const config = state.configuracaoBase;
  if (!config) {
    elemento('quiz-overlay').hidden = true;
    trocarVisao('study');
    return;
  }
  const botao = elemento('next-challenge');
  botao.disabled = true;
  const jornadaConcluida = Number(config.faseNaJornada || 1) >= Number(config.fasesPlanejadas || fasesPorQuantidade(config.quantidade));
  if (jornadaConcluida) {
    elemento('quiz-overlay').hidden = true;
    elemento('challenge-map-screen').hidden = true;
    document.body.classList.remove('map-open');
    trocarVisao('study');
    await atualizarPainel();
    mostrarToast('Jornada concluída! Você terminou todas as fases planejadas. Escolha um novo tema para continuar.');
    botao.disabled = false;
    return;
  }
  botao.textContent = 'Preparando próxima fase…';
  try {
    await criarProximoDesafio({ ...config, faseNaJornada: Number(config.faseNaJornada || 1) + 1, mostrarMapa: true });
  } catch (erro) {
    mostrarToast(`Não foi possível criar a próxima fase: ${erro.message}`);
  } finally {
    botao.disabled = false;
    const configAtual = state.configuracaoBase;
    if (configAtual) {
      const faseAtual = Number(configAtual.faseNaJornada || 1);
      const total = Number(configAtual.fasesPlanejadas || fasesPorQuantidade(configAtual.quantidade));
      botao.innerHTML = faseAtual >= total ? 'Concluir jornada <span>✓</span>' : `Próxima fase ${faseAtual + 1}/${total} <span>→</span>`;
    }
  }
});

function trocarVisao(visao) {
  const titulos = { study: 'Aprender', ranking: 'Ranking', progress: 'Meu progresso' };
  ['study', 'ranking', 'progress'].forEach((nome) => {
    elemento(`${nome}-view`).hidden = nome !== visao;
  });
  document.querySelectorAll('.nav-item[data-view]').forEach((botao) => botao.classList.toggle('active', botao.dataset.view === visao));
  elemento('page-heading').textContent = titulos[visao] || 'Aprender';
  elemento('sidebar').classList.remove('open');
  if (visao !== 'study') atualizarPainel().catch(() => {});
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

document.querySelectorAll('.nav-item[data-view]').forEach((botao) => botao.addEventListener('click', () => trocarVisao(botao.dataset.view)));
document.querySelectorAll('[data-go-view]').forEach((botao) => botao.addEventListener('click', () => trocarVisao(botao.dataset.goView)));
elemento('mobile-menu').addEventListener('click', () => elemento('sidebar').classList.toggle('open'));
document.addEventListener('click', (evento) => {
  const sidebar = elemento('sidebar');
  if (window.innerWidth <= 720 && sidebar.classList.contains('open') && !sidebar.contains(evento.target) && !elemento('mobile-menu').contains(evento.target)) sidebar.classList.remove('open');
});

function fecharMenuConta() {
  elemento('account-popover').hidden = true;
  elemento('logout-button').setAttribute('aria-expanded', 'false');
}

async function encerrarSessao(voltarAoLogin = true) {
  try { await api('/api/auth/logout', { method: 'POST', body: {} }); } catch (erro) { console.warn(erro); }
  state.aluno = null;
  state.progresso = null;
  pararContagemDeTempo();
  fecharMenuConta();
  mostrarTelaAutenticacao();
  trocarModoAutenticacao('login');
  elemento('login-form').reset();
  if (voltarAoLogin) elemento('login-form').querySelector('input[name="email"]').focus();
}

elemento('logout-button').addEventListener('click', (evento) => {
  evento.stopPropagation();
  const menu = elemento('account-popover');
  menu.hidden = !menu.hidden;
  elemento('logout-button').setAttribute('aria-expanded', String(!menu.hidden));
});
elemento('account-popover').addEventListener('click', async (evento) => {
  const botao = evento.target.closest('[data-account-action]');
  if (!botao) return;
  const acao = botao.dataset.accountAction;
  if (acao === 'logout') {
    fecharMenuConta();
    await encerrarSessao(false);
  } else if (acao === 'switch') {
    fecharMenuConta();
    await encerrarSessao(true);
    mostrarAviso('Entre com outra conta ou use o mesmo e-mail para voltar ao seu perfil.', 'success');
  } else if (acao === 'delete') {
    fecharMenuConta();
    const confirmou = window.confirm('Excluir sua conta permanentemente? Seu perfil, pontos e histórico serão apagados. Esta ação não pode ser desfeita.');
    if (!confirmou) return;
    const senha = window.prompt('Por segurança, digite sua senha para confirmar a exclusão:');
    if (senha === null || !senha) return;
    try {
      await api('/api/auth/delete-account', { method: 'DELETE', body: { senha } });
      state.aluno = null;
      state.progresso = null;
      pararContagemDeTempo();
      mostrarTelaAutenticacao();
      trocarModoAutenticacao('register');
      mostrarAviso('Conta excluída com sucesso.');
    } catch (erro) { mostrarToast(erro.message); }
  }
});
document.addEventListener('click', (evento) => {
  if (!elemento('account-popover').hidden && !elemento('account-popover').contains(evento.target) && !elemento('logout-button').contains(evento.target)) fecharMenuConta();
});

elemento('profile-form').addEventListener('submit', async (evento) => {
  evento.preventDefault();
  const nick = elemento('profile-nick').value.trim();
  const botao = evento.currentTarget.querySelector('button');
  botao.disabled = true;
  try {
    const dados = await api('/api/learning/profile', { method: 'PATCH', body: { nick } });
    state.aluno = { ...state.aluno, ...dados.aluno };
    atualizarIdentidade();
    mostrarAviso('Nick atualizado. Ele já aparece no seu perfil.', 'success', 'profile-message');
    await atualizarPainel();
  } catch (erro) {
    mostrarAviso(erro.message, 'error', 'profile-message');
  } finally {
    botao.disabled = false;
  }
});

function iniciarContagemDeTempo() {
  pararContagemDeTempo();
  state.heartbeat = setInterval(async () => {
    if (document.visibilityState !== 'visible' || !state.aluno) return;
    try {
      const dados = await api('/api/learning/activity', { method: 'POST', body: { segundos: 60 } });
      state.aluno.minutos_ativos = dados.minutos_ativos;
      state.aluno.sequencia_atual = dados.sequencia_atual;
      elemento('stat-minutes').textContent = formatarNumero(dados.minutos_ativos);
      elemento('sidebar-streak').textContent = `${dados.sequencia_atual} ${dados.sequencia_atual === 1 ? 'dia' : 'dias'}`;
      elemento('top-streak').textContent = dados.sequencia_atual;
      elemento('stat-streak').textContent = dados.sequencia_atual;
    } catch (erro) {
      console.warn('Não foi possível registrar o tempo ativo:', erro.message);
    }
  }, 60000);
}

function pararContagemDeTempo() {
  if (state.heartbeat) clearInterval(state.heartbeat);
  state.heartbeat = null;
}

function formatarNumero(valor) {
  return new Intl.NumberFormat('pt-BR').format(Number(valor) || 0);
}

function formatarData(valor) {
  if (!valor) return '—';
  const data = new Date(`${valor}T12:00:00`);
  return Number.isNaN(data.getTime()) ? valor : data.toLocaleDateString('pt-BR');
}

restaurarSessao();
