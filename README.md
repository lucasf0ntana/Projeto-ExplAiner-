# ExplAIner v13 — navegação aprimorada e revisão isolada

## Alterações desta versão
- Barra superior redesenhada com navegação mais clara, indicadores e botão de continuar destacado.
- Barra lateral com estados ativos/hover, ícones e área de conta refinados.
- Revisões marcadas como `[REFAZER]` não são tratadas como desafios ativos da jornada normal.
- O histórico e o botão de refazer ignoram sessões de revisão para evitar encadeamento de revisões.
- A geração local prioriza perguntas que o aluno ainda não viu no mesmo tema e dificuldade, evitando repetições até esgotar o banco local disponível.
- A geração por IA recebe os enunciados anteriores como contexto para reduzir repetição.

## Limites importantes
O banco local é demonstrativo e finito. Ele não consegue garantir diversidade ilimitada nem uma separação pedagógica perfeita entre Fácil, Normal e Difícil. Para uma variedade muito maior e questões novas contextualizadas, configure `OPENAI_API_KEY` no arquivo `.env`. Se o banco local não tiver questões suficientes para a quantidade solicitada, o sistema informa o limite em vez de inventar questões de outro tema.

## Executar
1. Crie e ative um ambiente virtual Python.
2. Execute `pip install -r requirements.txt`.
3. Copie `.env.example` para `.env` se necessário e configure as variáveis.
4. Execute `python backend/app.py`.
5. Abra `http://127.0.0.1:5000`.

## Testes
Execute `python -m unittest discover -s tests -v`.

O projeto é organizado com `backend/`, `frontend/` e `tests/` diretamente na raiz; não é necessário abrir uma pasta de versão aninhada.

---

# ExplAIner — aprendizagem gamificada

Aplicação web de estudo construída com Flask, SQLite, HTML, CSS e JavaScript. A nova área do estudante fica na rota `/`; as páginas de administração CRUD que já existiam continuam disponíveis pelos arquivos HTML originais.

## Ajustes da versão 12 — ações do desafio, mapa e conta

- O botão verde do topo agora aparece somente quando existe um desafio em andamento e serve para continuar o desafio salvo.
- O botão grande de continuar foi removido da área de configuração. O botão inferior fica maior e é identificado como “Gerar desafio” ou “Criar um novo desafio”, conforme exista um desafio ativo.
- O minimapa de conquistas ganha borda, trilha e detalhes coloridos conforme matéria, tema e fase selecionados.
- O menu da conta oferece “Sair do site”, “Utilizar outra conta” e “Excluir minha conta”.
- A exclusão da conta solicita confirmação e senha e remove os registros pessoais de respostas, histórico, ranking e desafios próprios associados à conta.
- A estrutura do ZIP foi organizada para que `backend/`, `frontend/` e `tests/` fiquem diretamente na raiz, sem uma pasta `explv9/` adicional.

## Funcionalidades adicionadas

- Cadastro e login com sessão de servidor e senha armazenada como hash.
- Nick público, perfil e alteração do nick.
- Catálogo organizado por matéria e tema, com temas iniciais inseridos automaticamente quando o catálogo está vazio.
- Desafios com 5, 10, 15 ou 20 questões e níveis Fácil, Normal e Difícil. A jornada mostra quantos desafios terá: 5 questões → 5 desafios; 10 → 4; 15 → 3; 20 → 2.
- Questões de múltipla escolha, validação da resposta no backend, explicação da resposta e pontos por acerto.
- Bônus de 25 pontos por concluir um desafio com 100% de acertos.
- Ranking por pontos, sequência de atividade diária, tempo ativo, precisão e quantidade de desafios concluídos.
- Mapa espacial de desafios em tela cheia, adaptado às referências visuais exportadas do Figma, com uma bolinha por questão; tocar/clicar na bolinha abre a questão correspondente.
- Progresso visual das bolinhas respondidas, trilha conectada e quatro variações de mapa, que se alternam conforme a fase avança. Tema claro por padrão, com opção de tema escuro.
- Histórico de desafios e registro de respostas individuais, com opção para refazer atividades anteriores.
- Elogio após cada resposta correta, mensagem especial a cada cinco acertos consecutivos e mensagens separadas ao concluir uma fase ou acertar tudo.
- A jornada termina após o número de desafios planejado para a quantidade de questões escolhida; o estudante pode iniciar uma nova jornada depois.
- Layout responsivo para desktop e celular.
- Login e cadastro por e-mail/senha, com senha armazenada em hash e telas de acesso separadas.
- Integração opcional com a API da OpenAI para gerar questões alinhadas à matéria, ao tema, à dificuldade e à quantidade selecionada.
- Modo local de demonstração quando não existe chave de API configurada.


### Ajustes visuais v8 — mapa horizontal e mundos temáticos

- O mapa de cada desafio foi redesenhado para desktop em formato horizontal, com progressão da esquerda para a direita e rolagem lateral quando há muitas questões.
- As bolinhas ficam conectadas por uma trilha curva; questões concluídas ganham estado visual próprio e os rótulos ficam visíveis em telas maiores.
- O minimapa do painel inicial também usa uma trilha horizontal e ocupa menos espaço vertical.
- Os cenários variam conforme a matéria/tema (matemática, ciências, história, geografia, idiomas ou outros) e também recebem uma variação pela fase. Os cenários são feitos com gradientes e camadas CSS locais, sem dependência de imagens externas ou carregamento do Google.
- Mantidos o fluxo de perguntas, o histórico, o ranking, o sistema de pontos e o modo claro/escuro.

## Requisitos

- Python 3.10 ou superior.
- Pacotes descritos em `requirements.txt`.
- Opcional: chave de API da OpenAI para geração dinâmica de questões. O uso da API pode gerar custos na conta associada à chave.

## Executar no Windows

Abra o terminal na pasta raiz deste projeto e execute:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
cd backend
py app.py
```

Acesse `http://127.0.0.1:5000/` no navegador. Não abra `estudar.html` diretamente pelo explorador de arquivos: a interface usa a API Flask e a sessão HTTP.

Se o PowerShell bloquear a ativação do ambiente virtual, use o terminal CMD e rode `.venv\Scripts\activate.bat`.

## Configurar geração por IA

Sem a chave, o aplicativo usa um banco local demonstrativo. Para gerar questões com a API da OpenAI, defina as variáveis de ambiente **antes de iniciar o backend**. No PowerShell:

```powershell
$env:OPENAI_API_KEY="sua-chave-de-api"
$env:OPENAI_MODEL="gpt-4o-mini"
$env:FLASK_SECRET_KEY="uma-chave-longa-e-aleatoria"
cd backend
py app.py
```

A variável `OPENAI_API_KEY` deve permanecer apenas no backend; não a coloque em `estudar.js`, no HTML nem em arquivos publicados. `OPENAI_MODEL` é opcional. A geração dinâmica depende de conectividade e de uma conta de API habilitada. Se uma solicitação de geração falhar, o sistema retorna ao banco local de demonstração e identifica essa origem na resposta.

Para produção, configure uma `FLASK_SECRET_KEY` forte, use HTTPS e defina `COOKIE_SECURE=1`. O segredo de desenvolvimento incluído como padrão não é adequado para implantação pública.

## Notas sobre dados existentes

Na inicialização, o aplicativo adiciona as colunas novas ao banco SQLite existente sem eliminar os registros anteriores. Senhas legadas em texto puro são convertidas para hash quando o usuário entra com sucesso; novas senhas já são armazenadas como hash. Faça uma cópia de `backend/instance/explainer.db` antes de usar o projeto sobre uma base importante.

O modo local foi pensado para testar a navegação e a mecânica de gamificação sem chave de IA. Ele seleciona questões de demonstração por área de conhecimento e não equivale à geração personalizada por IA para cada tema. Para conteúdo escolar específico, configure a API e valide as questões geradas antes de uso avaliativo.

## API principal

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/learning/me`
- `GET /api/learning/catalog`
- `POST /api/learning/challenges`
- `GET /api/learning/challenges/<id>`
- `POST /api/learning/challenges/<id>/answer`
- `POST /api/learning/challenges/<id>/complete`
- `POST /api/learning/activity`
- `GET /api/learning/ranking`
- `GET /api/learning/history`
- `PATCH /api/learning/profile`

A interface de estudante foi reorganizada em um painel compacto, com configuração do desafio e mapa de conquistas lado a lado, indicadores resumidos e histórico/ranking em blocos menores. O mapa do desafio abre depois da criação, cada bolinha abre uma questão e, depois da resposta, o estudante volta ao mapa. A reprodução usa as referências visuais exportadas do Figma e não sincroniza automaticamente com o arquivo Figma original.

### Limite importante do painel administrativo legado

As rotas CRUD antigas (`/alunos`, `/questoes`, `/temas`, `/desafio`, `/ranking` e rotas associadas) foram mantidas para não quebrar as telas administrativas que já existiam no ZIP e ainda não têm autorização por perfil. Por isso, este estado do projeto deve ser executado localmente para desenvolvimento; antes de publicar o servidor na internet, proteja essas rotas com autenticação/autorização administrativa e revise a exposição dos dados. O novo fluxo de estudante usa sessão, hash de senha e validação de respostas no servidor, mas isso não substitui a proteção das rotas administrativas antigas.


## Ajustes para desktop
A interface recebeu overrides responsivos para monitores: modal de questao ampliado, tipografia maior, feedback de resposta com contraste alto e estados correto/incorreto claramente identificados.

## Autenticação (e-mail e senha)

- O login e o cadastro usam as rotas `/api/auth/login` e `/api/auth/register`, com senha armazenada em hash.
- A tela apresenta dois modos exclusivos: **Entrar** e **Criar conta**. O formulário inativo fica removido do layout; erros como e-mail já cadastrado levam ao modo de login e mantêm o e-mail preenchido.
- Não há botão, rota ou dependência de autenticação Google nesta versão.
- A confirmação de novas contas por código de e-mail ou SMS não está ativa; isso exige configurar um provedor de envio e implementar a validação do token.

## Atualizações v9 — continuidade e variedade
- O botão verde de **Continuar desafio** é a ação principal quando há um desafio incompleto salvo na conta.
- O botão inferior passa a indicar **Criar um novo desafio** quando existe um desafio em andamento; um novo desafio passa a ser o ativo mais recente.
- O botão **Refazer último desafio** aparece após existir pelo menos um desafio concluído. Tentativas de refazer não concedem pontos nem bônus de desafio perfeito.
- O servidor expõe o desafio ativo da conta, incluindo questões respondidas, para restaurar o progresso após sair e entrar novamente.
- A geração por IA pede maior diversidade entre enunciados e separação mais clara entre níveis. O banco local demonstrativo ainda tem uma variedade limitada; para grande diversidade real por tema, configure `OPENAI_API_KEY`.

## Ajustes desta versão
- O modo de refazer abre novamente o mapa de revisão, permite sair de qualquer questão e não habilita avanço de fase.
- Tentativas marcadas como `[REFAZER]` não contam para calcular a próxima fase normal.
- O gerador local não usa perguntas genéricas de outra matéria quando não reconhece o tema; nesse caso, configure `OPENAI_API_KEY` para solicitar geração contextualizada.
- O mapa usa uma ilustração 2D local e não depende de imagens externas.
