import json
import os
import random
import urllib.error
import urllib.request

LETRAS = ("A", "B", "C", "D")

# Banco demonstrativo usado quando OPENAI_API_KEY não está configurada.
# As questões são agrupadas por área; para uso escolar real, configure a API de IA.
BANCO_LOCAL = {
    "Matemática": [
        ("Quanto é 25% de 200?", ["25", "40", "50", "75"], "C", "25% corresponde a um quarto; 200 ÷ 4 = 50."),
        ("Qual fração é equivalente a 1/2?", ["2/3", "3/4", "4/5", "2/4"], "D", "Multiplicando numerador e denominador de 1/2 por 2, obtemos 2/4."),
        ("Resolva: 3x + 5 = 20.", ["3", "5", "7", "15"], "B", "Subtraindo 5, 3x = 15; dividindo por 3, x = 5."),
        ("Qual é a área de um retângulo de lados 8 cm e 4 cm?", ["12 cm²", "24 cm²", "32 cm²", "64 cm²"], "C", "A área é base × altura: 8 × 4 = 32 cm²."),
        ("Qual é a média aritmética de 6, 8 e 10?", ["8", "9", "10", "24"], "A", "A média é (6 + 8 + 10) ÷ 3 = 8."),
        ("Qual é o resultado de 2³?", ["5", "6", "8", "9"], "C", "2³ significa 2 × 2 × 2, que resulta em 8."),
        ("Um produto de R$ 80 teve desconto de 10%. Qual é o preço final?", ["R$ 8", "R$ 70", "R$ 72", "R$ 78"], "C", "10% de 80 é 8; 80 − 8 = 72."),
        ("Qual é o perímetro de um quadrado de lado 6 cm?", ["12 cm", "18 cm", "24 cm", "36 cm"], "C", "O perímetro é 4 × 6 = 24 cm."),
        ("Qual número é primo?", ["21", "27", "29", "33"], "C", "29 só é divisível por 1 e por ele mesmo."),
        ("Qual é o valor de 7 × 8?", ["48", "54", "56", "64"], "C", "Sete vezes oito é 56."),
        ("Quanto é 3/4 em porcentagem?", ["25%", "50%", "75%", "80%"], "C", "3 ÷ 4 = 0,75, equivalente a 75%."),
        ("Qual é a raiz quadrada de 81?", ["7", "8", "9", "10"], "C", "9 × 9 = 81."),
        ("Se y = 2x e x = 7, quanto vale y?", ["9", "12", "14", "21"], "C", "Substituindo x por 7: y = 2 × 7 = 14."),
        ("Qual é a forma decimal de 3/10?", ["0,03", "0,3", "3,0", "30"], "B", "Três décimos são escritos como 0,3."),
        ("Um triângulo tem ângulos de 60° e 50°. Qual é o terceiro ângulo?", ["60°", "70°", "80°", "90°"], "B", "A soma dos ângulos internos de um triângulo é 180°; 180 − 110 = 70°."),
        ("Qual expressão representa o dobro de um número n acrescido de 4?", ["2(n + 4)", "n² + 4", "2n + 4", "n + 8"], "C", "O dobro é 2n; acrescentando 4, temos 2n + 4."),
        ("Qual é o MMC de 4 e 6?", ["2", "6", "12", "24"], "C", "O menor múltiplo positivo comum a 4 e 6 é 12."),
        ("Em um mapa na escala 1:100, 3 cm representam quantos centímetros reais?", ["30 cm", "100 cm", "300 cm", "3.000 cm"], "C", "Cada centímetro no mapa representa 100 cm reais; 3 × 100 = 300 cm."),
        ("Qual é a probabilidade de sair cara em uma moeda justa?", ["0%", "25%", "50%", "100%"], "C", "Há dois resultados equiprováveis: cara e coroa; a chance é 1/2."),
        ("Qual é o próximo número da sequência 2, 5, 8, 11...?", ["12", "13", "14", "15"], "C", "A sequência aumenta de 3 em 3; 11 + 3 = 14."),
    ],
    "Programação": [
        ("Qual é a função principal de uma variável?", ["Armazenar um valor", "Desligar o programa", "Criar uma rede", "Formatar o disco"], "A", "Uma variável associa um nome a um valor que pode ser usado no programa."),
        ("Qual estrutura costuma repetir um bloco de código?", ["if", "for", "return", "import"], "B", "Laços como for repetem instruções para uma sequência ou quantidade de vezes."),
        ("Em lógica booleana, o que representa o valor true?", ["Falso", "Nulo", "Verdadeiro", "Texto"], "C", "true representa uma condição verdadeira."),
        ("Qual estrutura permite executar código apenas se uma condição for verdadeira?", ["if", "while", "print", "class"], "A", "A estrutura if avalia uma condição antes de executar seu bloco."),
        ("O que é um algoritmo?", ["Uma sequência finita de passos", "Um tipo de monitor", "Uma linguagem de marcação", "Uma peça de hardware"], "A", "Um algoritmo descreve passos organizados para resolver um problema."),
        ("Para que serve uma função?", ["Agrupar instruções reutilizáveis", "Somente desenhar telas", "Aumentar a memória física", "Substituir o sistema operacional"], "A", "Funções encapsulam comportamentos que podem ser chamados quando necessário."),
        ("Qual tipo de dado costuma representar números inteiros?", ["Boolean", "String", "Integer", "Char"], "C", "Integer representa números inteiros em muitas linguagens."),
        ("O que significa depurar um programa?", ["Localizar e corrigir erros", "Apagar todo o código", "Instalar uma impressora", "Criar um usuário"], "A", "Depuração é o processo de encontrar e corrigir defeitos no código."),
        ("Qual linguagem é usada principalmente para estruturar o conteúdo de páginas web?", ["HTML", "SQL", "C", "Bash"], "A", "HTML define a estrutura semântica do conteúdo de uma página web."),
        ("Qual linguagem é usada para estilizar páginas web?", ["CSS", "SQL", "Python", "C#"], "A", "CSS controla apresentação, layout e aparência visual das páginas."),
        ("Em JavaScript, qual operador testa igualdade estrita?", ["=", "==", "===", "!="], "C", "=== compara valor e tipo sem conversão implícita."),
        ("Para que serve SQL?", ["Consultar e manipular dados relacionais", "Editar imagens vetoriais", "Compilar o kernel", "Criar cabos de rede"], "A", "SQL é usada para consultar e manipular dados em bancos relacionais."),
        ("O que é um loop infinito?", ["Um ciclo que não termina", "Um comentário", "Uma função matemática", "Um banco de dados"], "A", "É uma repetição cuja condição de saída nunca é atingida."),
        ("O que significa API?", ["Interface de Programação de Aplicações", "Arquivo Pessoal Interno", "Aplicativo de Processamento de Imagem", "Ambiente de Projeto Integrado"], "A", "API define meios para sistemas e componentes se comunicarem."),
        ("Qual estrutura costuma representar pares chave-valor?", ["Dicionário", "Fila de impressão", "Pilha física", "Comentário"], "A", "Dicionários ou mapas associam chaves a valores."),
        ("Qual é a finalidade de um teste automatizado?", ["Verificar comportamento com execução repetível", "Substituir documentação sempre", "Aumentar o tamanho do código", "Desativar os logs"], "A", "Testes automatizados validam comportamentos de forma repetível."),
        ("O que é um banco de dados?", ["Uma coleção organizada de dados", "Um compilador", "Um tipo de variável apenas", "Um cabo"], "A", "Banco de dados armazena dados de modo estruturado para consulta e gestão."),
        ("Qual é o resultado lógico de true AND false?", ["true", "false", "null", "Erro sempre"], "B", "AND só é verdadeiro quando ambos os operandos são verdadeiros."),
        ("O que um controle de versão como Git acompanha?", ["Alterações nos arquivos do projeto", "Temperatura do processador", "Consumo elétrico da tela", "Apenas imagens"], "A", "Git registra o histórico de mudanças em arquivos de um projeto."),
        ("Qual é o objetivo de um comentário no código?", ["Explicar trechos para leitores", "Executar a próxima função", "Criar tabela automaticamente", "Compactar arquivos"], "A", "Comentários documentam intenção e ajudam na manutenção do código."),
    ],
    "Português": [
        ("Qual opção apresenta um substantivo?", ["Rapidamente", "Beleza", "Correr", "Azulmente"], "B", "Beleza nomeia uma qualidade ou conceito, funcionando como substantivo."),
        ("Em 'A menina estudou bastante', qual é o verbo?", ["A", "menina", "estudou", "bastante"], "C", "Estudou indica uma ação realizada no passado."),
        ("Qual frase está pontuada corretamente?", ["Vamos comer, pessoal!", "Vamos, comer pessoal!", "Vamos comer pessoal?", "Vamos comer; pessoal"], "A", "A vírgula separa o vocativo 'pessoal' do restante da frase."),
        ("Qual palavra é sinônimo de 'conciso'?", ["Extenso", "Objetivo", "Confuso", "Repetitivo"], "B", "Conciso é aquilo que comunica com poucas palavras e precisão."),
        ("Qual palavra é antônimo de 'escasso'?", ["Raro", "Pouco", "Abundante", "Limitado"], "C", "Abundante indica grande quantidade, o oposto de escasso."),
        ("Qual alternativa contém um adjetivo?", ["Casa", "Cantar", "Gentil", "Ontem"], "C", "Gentil caracteriza um substantivo, por isso é adjetivo."),
        ("Na comunicação, qual é a função principal de uma conclusão?", ["Introduzir assunto novo sem relação", "Encerrar e sintetizar as ideias", "Apagar a tese", "Substituir todo o desenvolvimento"], "B", "A conclusão fecha a argumentação e retoma os pontos centrais."),
        ("Qual forma está corretamente acentuada?", ["Voce", "Público", "Ideiá", "Heroì"], "B", "Público é proparoxítona e recebe acento gráfico."),
        ("Em 'Embora estivesse cansado, continuou', 'embora' expressa ideia de:", ["Causa", "Concessão", "Finalidade", "Comparação"], "B", "Embora introduz uma concessão: algo ocorre apesar de um obstáculo."),
        ("Qual opção é um pronome pessoal?", ["Eles", "Mesa", "Cantar", "Verde"], "A", "Eles é pronome pessoal do caso reto."),
        ("Qual é o plural correto de 'cidadão'?", ["Cidadões", "Cidadães", "Cidadãos", "Cidadãoses"], "C", "O plural mais comum e normativo de cidadão é cidadãos."),
        ("O que é uma metáfora?", ["Comparação explícita sempre com 'como'", "Uso figurado por aproximação de sentidos", "Repetição de sons iniciais", "Omissão obrigatória de verbo"], "B", "A metáfora transfere sentido por uma relação de semelhança implícita."),
        ("Em 'O livro que comprei é ótimo', 'que' retoma:", ["ótimo", "comprei", "livro", "é"], "C", "O pronome relativo que retoma o antecedente 'livro'."),
        ("Qual opção está escrita corretamente?", ["Excessão", "Exceção", "Ecessão", "Exceçâo"], "B", "A grafia correta é exceção."),
        ("Qual elemento apresenta o ponto de vista defendido em um texto argumentativo?", ["Tese", "Legenda", "Índice", "Epígrafe apenas"], "A", "A tese é a ideia central que o texto procura defender."),
        ("Qual alternativa contém uma conjunção adversativa?", ["Portanto", "Mas", "Porque", "Quando"], "B", "Mas expressa contraste ou oposição entre ideias."),
        ("Qual palavra é oxítona?", ["Lâmpada", "Mesa", "Café", "Árvore"], "C", "Café tem a última sílaba tônica."),
        ("O que caracteriza a linguagem denotativa?", ["Sentido literal", "Sentido exclusivamente irônico", "Sentido sempre poético", "Uso obrigatório de rima"], "A", "A denotação utiliza o significado literal da palavra."),
        ("Qual gênero costuma defender publicamente uma causa ou reivindicação coletiva?", ["Carta aberta", "Receita culinária", "Bula", "Verbete técnico apenas"], "A", "A carta aberta é dirigida ao público para expor uma posição ou demanda."),
        ("Qual alternativa apresenta concordância adequada?", ["Fazem dois anos", "Houveram problemas", "Faz dois anos", "Existe muitas opções"], "C", "O verbo fazer indicando tempo decorrido é impessoal e fica no singular."),
    ],
    "Ciências": [
        ("Qual organela celular está associada à produção de energia por respiração celular?", ["Ribossomo", "Mitocôndria", "Lisossomo", "Complexo de Golgi"], "B", "A mitocôndria participa da respiração celular e da produção de ATP."),
        ("Qual gás as plantas absorvem principalmente na fotossíntese?", ["Oxigênio", "Nitrogênio", "Dióxido de carbono", "Hélio"], "C", "As plantas utilizam dióxido de carbono e água para produzir matéria orgânica."),
        ("Qual é a unidade básica da vida?", ["Átomo", "Célula", "Tecido", "Órgão"], "B", "A célula é a menor unidade estrutural e funcional dos seres vivos."),
        ("Qual planeta é conhecido como planeta vermelho?", ["Vênus", "Marte", "Júpiter", "Mercúrio"], "B", "O óxido de ferro presente na superfície dá a Marte a aparência avermelhada."),
        ("Ao nível do mar, a água pura entra em ebulição aproximadamente a:", ["0 °C", "50 °C", "100 °C", "200 °C"], "C", "A água pura ferve perto de 100 °C sob pressão atmosférica de 1 atm."),
        ("Qual órgão bombeia o sangue pelo corpo humano?", ["Pulmão", "Rim", "Coração", "Fígado"], "C", "O coração bombeia o sangue pela circulação pulmonar e sistêmica."),
        ("Qual é a principal fonte de energia para a maioria dos ecossistemas?", ["Lua", "Sol", "Vento lunar", "Núcleo da Terra apenas"], "B", "A energia solar sustenta a fotossíntese e muitas cadeias alimentares."),
        ("Qual mudança de estado transforma líquido em gás?", ["Solidificação", "Condensação", "Vaporização", "Fusão"], "C", "Vaporização é a passagem do estado líquido para o gasoso."),
        ("Qual molécula carrega informação genética na maioria dos seres vivos?", ["DNA", "Amido", "Glicose", "Água"], "A", "O DNA armazena informação genética hereditária."),
        ("Qual destes é um recurso renovável?", ["Carvão mineral", "Petróleo", "Energia solar", "Gás natural"], "C", "A energia solar é renovada continuamente pela radiação do Sol."),
        ("Qual é a função principal das raízes em muitas plantas?", ["Produzir som", "Absorver água e sais minerais", "Fazer a polinização", "Formar sementes diretamente"], "B", "As raízes ajudam na fixação e na absorção de água e sais minerais."),
        ("Qual partícula possui carga elétrica negativa?", ["Próton", "Nêutron", "Elétron", "Fóton sempre"], "C", "O elétron tem carga elétrica negativa."),
        ("Qual sistema do corpo humano realiza as trocas gasosas?", ["Digestório", "Respiratório", "Esquelético", "Endócrino"], "B", "O sistema respiratório permite captar oxigênio e eliminar dióxido de carbono."),
        ("Qual é o pH aproximado de uma solução neutra a 25 °C?", ["0", "3", "7", "14"], "C", "Em condições usuais, soluções neutras têm pH próximo de 7."),
        ("Como se chama a variedade de seres vivos em uma região?", ["Biodiversidade", "Erosão", "Evaporação", "Mimetismo apenas"], "A", "Biodiversidade corresponde à variedade de formas de vida."),
        ("Qual força atrai objetos com massa entre si?", ["Atrito", "Gravidade", "Empuxo apenas", "Tensão elétrica sempre"], "B", "A gravidade é a interação atrativa entre corpos com massa."),
        ("Qual é a fórmula química da água?", ["CO₂", "O₂", "H₂O", "NaCl"], "C", "Uma molécula de água contém dois átomos de hidrogênio e um de oxigênio."),
        ("O que acontece com partículas quando a temperatura de uma substância aumenta, em geral?", ["A energia cinética média diminui", "A energia cinética média aumenta", "A massa desaparece", "Os átomos deixam de existir"], "B", "A temperatura está relacionada à energia cinética média das partículas."),
        ("Qual destes animais é um mamífero?", ["Sapo", "Tubarão", "Golfinho", "Tartaruga"], "C", "Golfinhos são mamíferos: respiram por pulmões e amamentam seus filhotes."),
        ("Qual processo devolve vapor de água à atmosfera a partir de superfícies líquidas?", ["Evaporação", "Congelamento", "Precipitação", "Infiltração"], "A", "Na evaporação, a água líquida passa para o estado gasoso."),
    ],
    "História": [
        ("Qual acontecimento é tradicionalmente usado como marco inicial da Idade Moderna?", ["Queda de Constantinopla em 1453", "Revolução Francesa em 1789", "Fim da Segunda Guerra em 1945", "Independência do Brasil em 1822"], "A", "1453 é um marco convencional, embora a transição histórica tenha sido gradual."),
        ("Em que ano foi proclamada a Independência do Brasil?", ["1500", "1789", "1822", "1889"], "C", "A Independência do Brasil foi proclamada em 7 de setembro de 1822."),
        ("Qual foi uma característica central da Revolução Industrial?", ["Substituição das máquinas por trabalho manual", "Mecanização crescente da produção", "Fim imediato das cidades", "Desaparecimento do comércio"], "B", "A industrialização ampliou o uso de máquinas e transformou a produção e o trabalho."),
        ("Qual sistema econômico predominou na Europa medieval?", ["Feudalismo", "Fordismo", "Toyotismo", "Mercantilismo digital"], "A", "O feudalismo organizou grande parte da sociedade medieval europeia."),
        ("Qual movimento defendia ideias de razão e crítica à autoridade tradicional no século XVIII?", ["Iluminismo", "Romantismo apenas", "Futurismo", "Surrealismo"], "A", "O Iluminismo valorizou razão, debate e crítica a estruturas tradicionais."),
        ("A abolição legal da escravidão no Brasil ocorreu em que ano?", ["1822", "1850", "1888", "1889"], "C", "A Lei Áurea foi assinada em 13 de maio de 1888."),
        ("Qual civilização antiga se desenvolveu ao longo do rio Nilo?", ["Egípcia", "Inca", "Asteca", "Fenícia exclusivamente"], "A", "O rio Nilo foi fundamental à agricultura e à organização do Egito antigo."),
        ("Qual foi o principal objetivo das grandes navegações europeias, entre outros?", ["Buscar rotas comerciais marítimas", "Eliminar toda navegação", "Criar a internet", "Encerrar o comércio de especiarias"], "A", "A busca por rotas para comércio e acesso a produtos foi um importante motor das navegações."),
        ("Qual evento iniciou a Primeira Guerra Mundial em 1914 como estopim imediato?", ["Invasão da Polônia", "Assassinato do arquiduque Francisco Ferdinando", "Queda do Muro de Berlim", "Ataque a Pearl Harbor"], "B", "O assassinato do arquiduque em Sarajevo desencadeou a crise de julho de 1914."),
        ("Qual foi uma consequência política da Revolução Francesa?", ["Fortalecimento dos privilégios feudais sem mudanças", "Questionamento da monarquia absolutista e dos privilégios", "Restauração do Império Romano", "Fim de todos os conflitos europeus"], "B", "A revolução transformou instituições políticas e difundiu ideias de cidadania e igualdade jurídica."),
        ("Qual povo desenvolveu a escrita cuneiforme na Mesopotâmia antiga?", ["Sumérios", "Maias", "Incas", "Vikings"], "A", "A escrita cuneiforme surgiu entre os sumérios na Mesopotâmia."),
        ("O que foi o apartheid na África do Sul?", ["Política de segregação racial", "Acordo de livre navegação medieval", "Sistema de votação universal desde o início", "Reforma agrícola do Império Romano"], "A", "O apartheid institucionalizou a segregação racial e a desigualdade de direitos."),
        ("Qual documento inglês de 1215 limitou certos poderes do rei?", ["Magna Carta", "Tratado de Versalhes", "Carta da ONU", "Código de Hamurábi"], "A", "A Magna Carta impôs limites e obrigações ao rei João da Inglaterra."),
        ("Qual período histórico veio após a Antiguidade na divisão tradicional europeia?", ["Idade Média", "Idade Contemporânea", "Pré-História", "Era Digital"], "A", "Na divisão tradicional, a Idade Média sucede à Antiguidade."),
        ("Qual foi uma característica do colonialismo europeu nas Américas?", ["Exploração de recursos e imposição de estruturas de poder", "Ausência de conflitos", "Igualdade política plena", "Independência imediata de todas as colônias"], "A", "O colonialismo envolveu exploração econômica e relações assimétricas de poder."),
        ("A Proclamação da República no Brasil ocorreu em:", ["1808", "1822", "1888", "1889"], "D", "A República foi proclamada em 15 de novembro de 1889."),
        ("Qual foi uma característica do Renascimento cultural europeu?", ["Valorização de referências clássicas e do humanismo", "Proibição de toda investigação científica", "Adoção da internet", "Fim de toda produção artística"], "A", "O Renascimento valorizou as culturas clássicas, as artes e o ser humano."),
        ("Qual organização foi criada em 1945 para promover cooperação internacional e paz?", ["ONU", "Liga Hanseática", "OTAN em 1910", "Mercosul"], "A", "A Organização das Nações Unidas foi fundada em 1945."),
        ("Qual foi uma consequência da chegada dos portugueses em 1500 para os povos indígenas?", ["Contato sem mudanças", "Transformações profundas, conflitos e perda de territórios", "Fim imediato das línguas indígenas", "Ausência de epidemias"], "B", "A colonização produziu impactos demográficos, territoriais e culturais profundos."),
        ("A Guerra Fria foi marcada principalmente pela rivalidade entre:", ["Estados Unidos e União Soviética", "Brasil e Argentina", "Roma e Cartago", "Portugal e Espanha no século XV"], "A", "A disputa geopolítica e ideológica entre EUA e URSS marcou a Guerra Fria."),
    ],
    "Geografia": [
        ("Qual é a camada mais externa e sólida da Terra?", ["Núcleo interno", "Núcleo externo", "Crosta terrestre", "Manto inferior apenas"], "C", "A crosta é a camada mais externa da estrutura interna terrestre."),
        ("Qual linha imaginária divide a Terra em hemisférios Norte e Sul?", ["Meridiano de Greenwich", "Linha do Equador", "Trópico de Capricórnio", "Círculo Polar Ártico"], "B", "A Linha do Equador divide os hemisférios Norte e Sul."),
        ("Qual é a capital do Brasil?", ["São Paulo", "Rio de Janeiro", "Brasília", "Salvador"], "C", "Brasília é a capital federal do Brasil desde 1960."),
        ("Qual bioma brasileiro é conhecido por sua vegetação adaptada à seca?", ["Caatinga", "Pampa", "Mata de Araucárias", "Pantanal apenas"], "A", "A Caatinga apresenta espécies adaptadas à disponibilidade irregular de água."),
        ("O que mede a densidade demográfica?", ["Habitantes por unidade de área", "Nascimentos por ano apenas", "Área total de rios", "Temperatura média anual"], "A", "Densidade demográfica é a relação entre população e área."),
        ("Qual fenômeno explica o deslocamento de massas de ar e influencia o tempo?", ["Circulação atmosférica", "Tectônica de placas apenas", "Fotossíntese", "Erosão costeira somente"], "A", "A circulação atmosférica transporta calor e umidade e influencia o tempo e o clima."),
        ("Qual região brasileira possui a maior parte da Floresta Amazônica?", ["Norte", "Sul", "Sudeste", "Centro-Sul"], "A", "A Amazônia ocupa grande parte da Região Norte, além de áreas de outras regiões."),
        ("Qual movimento da Terra explica a alternância de dias e noites?", ["Translação", "Rotação", "Precessão apenas", "Deriva continental"], "B", "A rotação da Terra em torno de seu eixo gera a alternância entre dia e noite."),
        ("Qual é a principal causa das estações do ano?", ["Variação da distância Terra-Sol como único fator", "Inclinação do eixo terrestre combinada à translação", "Rotação da Lua", "Mudanças nas marés"], "B", "A inclinação do eixo e a translação alteram a incidência solar ao longo do ano."),
        ("Qual é um exemplo de fonte de energia não renovável?", ["Solar", "Eólica", "Petróleo", "Marés"], "C", "O petróleo é um combustível fóssil formado em escalas de milhões de anos."),
        ("O que é êxodo rural?", ["Migração do campo para a cidade", "Mudança de país para país apenas", "Migração da cidade para o campo", "Deslocamento de animais"], "A", "Êxodo rural é a saída de população das áreas rurais, frequentemente rumo às cidades."),
        ("Qual agente modela o relevo ao transportar sedimentos em rios?", ["Água corrente", "Som", "Campo magnético apenas", "Luz visível"], "A", "Rios erodem, transportam e depositam sedimentos, modificando o relevo."),
        ("Qual oceano banha a costa leste do Brasil?", ["Pacífico", "Índico", "Atlântico", "Ártico"], "C", "A costa brasileira é banhada pelo Oceano Atlântico."),
        ("Qual mapa é especialmente adequado para mostrar fronteiras políticas?", ["Mapa político", "Mapa de precipitação apenas", "Mapa batimétrico", "Mapa de vegetação apenas"], "A", "Mapas políticos representam divisões territoriais e fronteiras administrativas."),
        ("O aquecimento global atual está associado principalmente ao aumento de:", ["Gases de efeito estufa por atividades humanas", "Oxigênio na estratosfera apenas", "Salinidade do oceano apenas", "Rotação terrestre"], "A", "Emissões humanas de gases de efeito estufa intensificam o aquecimento do sistema climático."),
        ("Qual fenômeno é o desgaste e transporte de materiais da superfície terrestre?", ["Erosão", "Condensação", "Fotossíntese", "Magnetização"], "A", "A erosão envolve remoção e transporte de partículas por água, vento, gelo ou gravidade."),
        ("Qual é a principal característica de uma metrópole?", ["Influência econômica e funcional sobre ampla área", "População sempre menor que vila", "Ausência de serviços", "Localização obrigatória no campo"], "A", "Metrópoles concentram funções e influenciam redes urbanas mais amplas."),
        ("Qual região brasileira é a menor em área territorial?", ["Norte", "Nordeste", "Sul", "Centro-Oeste"], "C", "A Região Sul é a menor das cinco grandes regiões do Brasil em área."),
        ("O que representa a latitude?", ["Distância angular em relação ao Equador", "Distância em relação ao meridiano de Greenwich", "Altura de uma montanha apenas", "Profundidade oceânica"], "A", "A latitude é medida ao norte ou ao sul do Equador."),
        ("Qual processo está ligado à formação de montanhas pela interação das placas tectônicas?", ["Orogênese", "Evaporação", "Sedimentação exclusivamente marinha", "Transpiração"], "A", "A orogênese envolve deformações da crosta e formação de cadeias montanhosas."),
    ],
}


def _validar_questoes(questoes, quantidade):
    if not isinstance(questoes, list) or len(questoes) < quantidade:
        raise ValueError("A IA não retornou a quantidade solicitada de questões.")
    normalizadas = []
    for item in questoes[:quantidade]:
        enunciado = str(item.get("enunciado", "")).strip()
        alternativas = item.get("alternativas", {})
        correta = str(item.get("alternativa_correta", "")).upper().strip()
        if isinstance(alternativas, list) and len(alternativas) == 4:
            alternativas = dict(zip(LETRAS, alternativas))
        if not enunciado or not isinstance(alternativas, dict) or any(not str(alternativas.get(letra, "")).strip() for letra in LETRAS):
            raise ValueError("Questão incompleta recebida da IA.")
        if correta not in LETRAS:
            raise ValueError("Alternativa correta inválida recebida da IA.")
        normalizadas.append({
            "enunciado": enunciado,
            "alternativas": {letra: str(alternativas[letra]).strip() for letra in LETRAS},
            "alternativa_correta": correta,
            "explicacao": str(item.get("explicacao", "")).strip() or "Revise o conceito apresentado para compreender a resposta correta.",
        })
    return normalizadas


def _gerar_com_openai(materia, tema, dificuldade, quantidade, excluir_enunciados=None):
    chave = os.getenv("OPENAI_API_KEY", "").strip()
    if not chave:
        return None
    modelo = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    prompt = f"""Crie exatamente {quantidade} questões de múltipla escolha em português brasileiro.
Matéria: {materia}. Tema específico: {tema}. Dificuldade: {dificuldade}.
As questões devem ser educacionalmente corretas, distintas, relevantes ao tema e apropriadas a estudantes.
Cada questão deve ter quatro alternativas plausíveis A, B, C e D, apenas uma correta, e explicação curta.
Não use 'todas as anteriores' nem 'nenhuma das anteriores'. Não repita enunciados, exemplos, números, contexto ou estrutura dentro deste lote.
Varie deliberadamente os subtemas, situações-problema, formatos de raciocínio e exemplos. Não use perguntas genéricas que só mencionem o tema no texto. TODA questão precisa testar diretamente um conceito do tema específico; se o tema for "corpo humano", não pergunte sobre planetas, clima ou fotossíntese. Antes de retornar, confira individualmente que cada enunciado, resposta e explicação pertence à matéria E ao tema. Se não houver conteúdo suficiente para criar questões corretas, gere variações de raciocínio dentro do próprio tema, nunca mude para outro assunto.
A dificuldade precisa mudar o tipo de raciocínio: Fácil = conceitos fundamentais e identificação; Normal = aplicação, interpretação e relações entre conceitos; Difícil = análise, inferência e resolução em várias etapas. Evite reutilizar a mesma pergunta em dificuldades diferentes.
Enunciados já usados que devem ser evitados nesta nova tentativa: {json.dumps((excluir_enunciados or [])[:80], ensure_ascii=False)}.
Não copie nem reformule superficialmente essas perguntas; crie questões novas dentro do mesmo tema.
Retorne exclusivamente JSON neste formato:
{{"questoes":[{{"enunciado":"...","alternativas":{{"A":"...","B":"...","C":"...","D":"..."}},"alternativa_correta":"A","explicacao":"..."}}]}}
"""
    payload = {
        "model": modelo,
        "messages": [
            {"role": "system", "content": "Você é um elaborador rigoroso de questões educacionais. Priorize precisão factual e siga exatamente o formato JSON solicitado."},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.9,
        "max_completion_tokens": 5000,
    }
    requisicao = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {chave}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(requisicao, timeout=50) as resposta:
            retorno = json.loads(resposta.read().decode("utf-8"))
        conteudo = retorno["choices"][0]["message"]["content"]
        return _validar_questoes(json.loads(conteudo)["questoes"], quantidade)
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError, ValueError) as erro:
        raise RuntimeError(f"Não foi possível gerar questões pela API de IA: {erro}") from erro


BANCO_TEMATICO = {
    "corpo humano": [
        ("Qual órgão bombeia o sangue para a circulação?", ["Pulmão", "Coração", "Estômago", "Rim"], "B", "O coração impulsiona o sangue pelos vasos sanguíneos."),
        ("Em qual estrutura ocorre a maior parte da absorção dos nutrientes?", ["Intestino delgado", "Esôfago", "Traqueia", "Bexiga"], "A", "As vilosidades do intestino delgado ampliam a absorção dos nutrientes."),
        ("Qual é a principal função dos alvéolos pulmonares?", ["Produzir bile", "Filtrar a urina", "Realizar trocas gasosas", "Bombear sangue"], "C", "Nos alvéolos, oxigênio e gás carbônico são trocados entre ar e sangue."),
        ("Qual sistema coordena respostas rápidas por meio de impulsos nervosos?", ["Digestório", "Nervoso", "Urinário", "Esquelético"], "B", "O sistema nervoso transmite sinais elétricos e químicos."),
        ("Qual célula transporta a maior parte do oxigênio no sangue?", ["Neurônio", "Hemácia", "Plaqueta", "Osteócito"], "B", "A hemoglobina das hemácias transporta a maior parte do oxigênio."),
        ("Qual órgão produz a bile, que auxilia na digestão de gorduras?", ["Pâncreas", "Fígado", "Baço", "Rim"], "B", "O fígado produz a bile, armazenada e concentrada na vesícula biliar."),
        ("Qual é a função principal dos rins?", ["Produzir movimentos", "Filtrar o sangue e formar urina", "Realizar trocas gasosas", "Digerir proteínas no estômago"], "B", "Os rins removem resíduos do sangue e ajudam a regular água e sais."),
        ("Onde ocorre a troca de oxigênio e gás carbônico entre o ar e o sangue?", ["Alvéolos", "Tendões", "Ventrículos intestinais", "Articulações"], "A", "A parede fina dos alvéolos permite a difusão dos gases."),
        ("Qual estrutura liga músculos aos ossos?", ["Ligamento", "Tendão", "Cartilagem articular", "Neurônio"], "B", "Tendões conectam músculos aos ossos e transmitem força."),
        ("Qual tipo de músculo atua principalmente de forma involuntária no intestino?", ["Esquelético", "Liso", "Voluntário estriado", "Nenhum"], "B", "A musculatura lisa movimenta o conteúdo do tubo digestório involuntariamente."),
        ("Qual parte do cérebro participa de forma importante do equilíbrio e da coordenação?", ["Cerebelo", "Hipófise", "Medula óssea", "Laringe"], "A", "O cerebelo contribui para coordenação motora, postura e equilíbrio."),
        ("Qual componente do sangue participa da coagulação?", ["Plaquetas", "Alvéolos", "Bile", "Neurônios"], "A", "As plaquetas ajudam a formar o tampão inicial na coagulação."),
        ("Qual é a sequência correta do caminho do alimento após a boca?", ["Faringe, esôfago, estômago", "Traqueia, pulmão, estômago", "Rim, ureter, bexiga", "Coração, artéria, estômago"], "A", "Após a boca, o alimento passa pela faringe, esôfago e estômago."),
        ("Que estrutura protege o cérebro?", ["Costelas", "Crânio", "Pelve", "Esterno"], "B", "Os ossos do crânio envolvem e protegem o encéfalo."),
        ("Qual hormônio ajuda a reduzir a glicose no sangue?", ["Insulina", "Adrenalina", "Melatonina", "Tiroxina"], "A", "A insulina favorece a entrada de glicose em células e reduz sua concentração sanguínea."),
        ("Por que a frequência cardíaca aumenta durante exercícios?", ["O corpo precisa levar mais oxigênio aos tecidos", "Os rins param de funcionar", "O estômago passa a respirar", "Os ossos produzem ar"], "A", "Os músculos ativos precisam de mais oxigênio e nutrientes, exigindo maior fluxo sanguíneo."),
        ("Como o diafragma contribui para a inspiração?", ["Contrai e aumenta o volume torácico", "Fecha os rins", "Diminui a caixa torácica ao relaxar", "Impede o ar de entrar"], "A", "Ao contrair, o diafragma desce e amplia o volume do tórax."),
        ("O que acontece com a urina antes de chegar à bexiga?", ["Passa pelos ureteres", "Passa pela traqueia", "Vai pelo esôfago", "É bombeada pela aorta"], "A", "Os ureteres conduzem a urina dos rins até a bexiga."),
        ("Qual relação descreve corretamente neurônios e sinapses?", ["Sinapses permitem comunicação entre células nervosas", "Sinapses filtram a urina", "Neurônios produzem bile", "Neurônios são ossos"], "A", "Sinapses são regiões de comunicação entre neurônios ou entre neurônios e outras células."),
        ("Por que as articulações são importantes para o movimento?", ["Permitem conexão e movimento relativo entre ossos", "Produzem glóbulos vermelhos em todos os casos", "Bombeiam sangue", "Fazem a digestão química"], "A", "As articulações conectam ossos e permitem movimentos de diferentes amplitudes."),
    ]
}

def _gerar_local(materia, tema, quantidade, dificuldade="Normal", excluir_enunciados=None):
    nome = str(materia or "").strip().casefold()
    categorias = {
        "matemática": "Matemática", "matematica": "Matemática",
        "programação": "Programação", "programacao": "Programação", "desenvolvimento web": "Programação",
        "português": "Português", "portugues": "Português", "língua portuguesa": "Português",
        "ciências": "Ciências", "ciencias": "Ciências", "biologia": "Ciências", "física": "Ciências", "química": "Ciências",
        "história": "História", "historia": "História",
        "geografia": "Geografia",
    }
    categoria = next((valor for chave, valor in categorias.items() if chave in nome), "Ciências")
    tema_normalizado = str(tema or "").strip().casefold()
    base_tematica = next((questoes for nome_tema, questoes in BANCO_TEMATICO.items() if nome_tema in tema_normalizado), None)
    if base_tematica:
        base = base_tematica
    else:
        # O banco genérico só pode ser usado quando o próprio tema corresponde à categoria.
        palavras_categoria = {
            "Matemática": ("matem", "álgebra", "geometr", "fração", "porcentagem", "equação"),
            "Programação": ("program", "código", "algorit", "python", "javascript", "html", "css", "sql", "lógica"),
            "Português": ("portugu", "gramática", "verbo", "substantivo", "interpretação de texto", "literatura", "acentuação"),
            "Ciências": ("ciência", "biolog", "química", "física", "ecologia", "fotossíntese", "célula", "genética", "corpo humano", "sistema digestório", "sistema respiratório"),
            "História": ("história", "guerra", "revolução", "império", "idade média", "colonização", "independência"),
            "Geografia": ("geografia", "clima", "relevo", "continente", "cartografia", "população", "urbanização"),
        }
        if not any(palavra in tema_normalizado for palavra in palavras_categoria.get(categoria, ())):
            raise RuntimeError(f"Não há banco local confiável para o tema '{tema}'. Configure OPENAI_API_KEY para gerar questões específicas, em vez de receber perguntas de outro assunto.")
        base = BANCO_LOCAL[categoria]
    # Seleciona primeiro perguntas nunca vistas por este aluno neste tema/dificuldade.
    # O banco demonstrativo não possui tags pedagógicas suficientes para separar perfeitamente
    # cada nível; a separação rigorosa por dificuldade é feita pela IA quando configurada.
    excluir = {str(texto).strip().casefold() for texto in (excluir_enunciados or []) if texto}
    novas = [questao for questao in base if questao[0].strip().casefold() not in excluir]
    antigas = [questao for questao in base if questao[0].strip().casefold() in excluir]
    random.shuffle(novas)
    random.shuffle(antigas)
    questoes = novas + antigas
    selecionadas = questoes[:min(quantidade, len(questoes))]
    # Evita duplicar enunciados dentro do mesmo desafio. Se o banco for menor que o pedido,
    # completa com questões já vistas somente depois de esgotar as inéditas.
    while len(selecionadas) < quantidade:
        disponiveis = [q for q in base if q[0] not in {item[0] for item in selecionadas}]
        if not disponiveis:
            break
        random.shuffle(disponiveis)
        selecionadas.extend(disponiveis[:quantidade - len(selecionadas)])
    if len(selecionadas) < quantidade:
        raise RuntimeError(
            f"O banco local tem apenas {len(base)} questões para '{tema}', insuficientes para montar "
            f"{quantidade} questões sem repetição. Configure OPENAI_API_KEY para ampliar a variedade."
        )
    saida = []
    tema_limpo = str(tema or "").strip()
    for indice in range(quantidade):
        enunciado, opcoes, correta, explicacao = selecionadas[indice]
        opcoes = list(opcoes)
        resposta_correta = opcoes[LETRAS.index(correta)]
        random.shuffle(opcoes)
        letra_correta = LETRAS[opcoes.index(resposta_correta)]
        # O contexto do tema aparece no desafio sem afirmar que toda pergunta
        # do banco local foi criada especificamente para ele.
        saida.append({
            "enunciado": enunciado,
            "alternativas": dict(zip(LETRAS, opcoes)),
            "alternativa_correta": letra_correta,
            "explicacao": explicacao,
        })
    return saida


def gerar_questoes(materia, tema, dificuldade, quantidade, excluir_enunciados=None):
    erro_ia = None
    try:
        geradas = _gerar_com_openai(materia, tema, dificuldade, quantidade, excluir_enunciados)
        if geradas:
            return geradas, "ia", None
    except RuntimeError as erro:
        erro_ia = str(erro)
    return _gerar_local(materia, tema, quantidade, dificuldade, excluir_enunciados), "banco_local", erro_ia
