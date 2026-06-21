import pandas as pd
import joblib
import sys
import os
import json
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix, make_scorer
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ia.preprocess import clean_text

# ══════════════════════════════════════════════════════════════════════
# DATASET DE TREINAMENTO — v3.0 EXPANDIDO (600+ AMOSTRAS)
# ══════════════════════════════════════════════════════════════════════
# Estratégia:
# - Adulto: ~250 amostras com ampla cobertura de gírias, eufemismos,
#   grooming, drogas, violência, camuflagem e variações semânticas.
# - Infantil: ~180 amostras para evitar falsos positivos (FP).
# - Neutro: ~170 amostras com contextos adultos mas não NSFW.
#
# Meta: Recall >= 85% na classe "adulto" (redução de falsos negativos).
# ══════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────
# CLASSE: INFANTIL (conteúdo seguro para crianças)
# ─────────────────────────────────────────────────────────────────────
dados_infantil = [
    # Escola e aprendizado
    "Brincando no parque com meus amigos da escola",
    "Estudando matemática para a prova de amanhã",
    "Fazendo tarefa da escola de ciências naturais",
    "Aprendendo o alfabeto na creche hoje",
    "A professora ensinou a tabuada do sete",
    "Pintei um desenho lindo na aula de artes",
    "Hoje aprendi sobre os planetas do sistema solar",
    "Fiz uma redação sobre minha família",
    "A prova de português foi muito fácil",
    "Aprendi a somar e subtrair frações na escola",
    "A professora de história contou sobre os índios",
    "Hoje tivemos aula de educação física na quadra",
    "Ganhe nota dez na prova de ciências",
    "Estou estudando para o ENEM de graça pelo youtube",
    "A escola fez um passeio ao museu de arte",
    "Aula de música aprendendo flauta doce",
    "Fiz uma maquete do sistema solar com isopor",
    "Amanhã tem feira de ciências na escola",
    "Ganhei o primeiro lugar na olimpíada de matemática",
    "A professora de inglês ensinou as cores em inglês",

    # Brincadeiras e atividades lúdicas
    "Jogando bola com amigos no recreio da escola",
    "Brincadeira de esconde-esconde no quintal de casa",
    "Colorindo desenhos de dinossauros e animais",
    "Montando quebra-cabeça de quinhentas peças",
    "Fiz uma torre de lego muito alta e colorida",
    "Brincando com massinha de modelar fazendo bolo",
    "Joguei amarelinha no intervalo com as amigas",
    "Brinquedo de pelúcia favorito é o urso de pelúcia",
    "Colecionando figurinhas do álbum de futebol",
    "Adorei brincar de pula-corda no recreio hoje",
    "Construindo castelo de areia na praia com pai",
    "Pescaria de brinquedo na banheira com o irmão",
    "Adoro brincar de pega-pega com os primos",
    "Jogo de tabuleiro xadrez com o vovô no domingo",
    "Voamos pipa no parque com o vento forte",
    "Brincando de casinha com minha amiga vizinha",
    "Andando de patins pela calçada da rua",
    "Estou aprendendo a andar de bicicleta sem rodinhas",
    "Jogando bafo de figurinhas na escola hoje",
    "Brincamos de teatro na aula de artes dramáticas",

    # Animais, natureza e curiosidades
    "Meu cachorrinho labrador é muito fofo e brinca",
    "O gatinho dormiu no meu colo assistindo TV",
    "Fui ao zoológico ver leões elefantes e girafas",
    "Temos um peixinho dourado no aquário de casa",
    "Plantamos feijão no algodão para observar crescer",
    "Encontrei uma lagarta e virou borboleta colorida",
    "O coelho da escola é muito fofo e come cenoura",
    "Vi um passarinho construindo ninho na árvore",
    "A joaninha tem sete pontos vermelhos nas asas",
    "Minha tartaruga come alface e se move devagar",

    # Personagens, filmes e desenhos infantis (Hard Negatives anti-FP)
    "Assisti episódios da Peppa Pig animada ontem",
    "Amo ler os quadrinhos da Turma da Monica",
    "Minha personagem favorita da Monica é a Magali",
    "Patrulha Canina está passando agora na televisão",
    "Jogando Roblox e Minecraft a tarde inteira",
    "Galinha Pintadinha é muito engraçada e colorida",
    "Mundo Bita tem musica de bom dia bem divertida",
    "Assistindo filme da Disney no cinema com familia",
    "Bob Esponja mora no abacaxi no fundo do mar",
    "Gosto das princesas da Disney fadas e castelo",
    "Os Smurfs são azuis e moram na floresta encantada",
    "Ben Ten transforma em aliens para salvar o mundo",
    "Hora de Aventura com Finn e Jake é muito legal",
    "Polly Pocket tem casa minuscula e bonecas pequenas",
    "Lego Ninjago os ninjas lutam contra o mal sempre",
    "Tom e Jerry sempre se perseguem na televisao",
    "Scooby Doo e seus amigos resolvem misterios assustadores",
    "Filme do Homem Aranha infantil sem violencia",
    "Sonic the Hedgehog corre muito rapido nos jogos",
    "Assistindo o Rei Leao pela decima vez hoje",
    "Pikachu e meu pokemon favorito de todos",
    "Assistir Dragon Ball Z com o meu irmao mais velho",

    # Alimentação, rotina e família
    "Mamae fez bolo de chocolate de aniversario gostoso",
    "Quero beber chocolate quente antes de dormir",
    "Tomei leite com nescau no cafe da manha hoje",
    "Bebi suco de laranja fresquinho no almoco feliz",
    "Comi sorvete de morango com minha familia",
    "Passeando com meus pais no shopping novo",
    "Festa de aniversario com baloes coloridos e bolo",
    "Ganhei um brinquedo novo de aniversario da vovo",
    "Meu pai me levou ao parque de diversoes",
    "A vovo fez biscoito de mel gostoso para merendar",
    "Domingo eh dia de churrasco com familia reunida",
    "Dormindo cedo porque amanha tem escola de manha",
    "Tomando banho antes de dormir para estar limpo",
    "Escovei os dentes depois de comer para nao caries",
    "Rezei antes de dormir agradecendo pela familia",
    "Minha familia foi na missa domingo de manha",
    "Fomos ao supermercado comprar frutas e verduras",
    "Ajudei a mae a dobrar roupas da lavanderia",
    "Reguei as plantas do quintal de manha cedo",
    "Pai me ensinou a fazer brigadeiro gostoso hoje",

    # Textos benignos com possíveis homônimos (Hard Negatives)
    "Minha gatinha subiu na arvore mais alta do quintal",
    "Vou comer um doce de banana delicioso hoje",
    "Bebê tomando banho de banheira na agua morna",
    "Meninas brincando de boneca juntas na sala",
    "Aula de reproducao das plantas em ciencias biologicas",
    "A obra de arte classica mostrava corpo humano no museu",
    "Crianca na piscina brincando na agua no verao",
    "Jogando peteca no quintal com minha prima hoje",
    "Livro infantil do Monteiro Lobato com Emilia e Narizinho",
    "Turma do Chaves e muito engraçada e divertida",
    "Fazendo origami de passarinho com papel colorido",
    "Assistindo um filme animacao da Pixar com familia",
    "Brincando de medico com o kit de brinquedo",
    "Lendo gibi da Turma da Monica com minha irma",
    "Coleciono cards do Pokemon desde pequeno",
    "Comprei uma bola de futebol nova no shopping",
    "Aprendi a nadar no curso de natacao infantil",
    "Fui ao parque aquatico com a escola no final de ano",
    "Ganhei um livro de historias de fadas no natal",
    "Brincando de esconder o tesouro no jardim da escola",

    # ── HARD NEGATIVES v4.0 (vocabulário ambíguo em contexto inocente) ──
    # Objetivo: ensinar o modelo a NÃO bloquear palavras como "gostoso",
    # "delicia", "comer", "beijo", "amor", "pelada" (futebol), "lamber"
    # quando aparecem em contextos infantis claramente inofensivos.
    "O bolo de chocolate da vovo ficou super gostoso e fofo",
    "Que delicia esse sorvete de morango da sorveteria",
    "Vou comer um pedaco de bolo de aniversario agora",
    "Minha mae me deu um beijo de boa noite antes de dormir",
    "Amo demais meus pais e meu irmaozinho bebe",
    "O cachorro lambeu meu rosto todinho de manha cedo",
    "Comi um picole de uva delicioso no calor de hoje",
    "Joguei uma pelada de futebol com a galera no campinho da escola",
    "Sentei no chao pra montar o quebra cabeca gigante",
    "Que sono gostoso depois de brincar a tarde inteira",
    "Mamae fez uma comida deliciosa pro meu almoco",
    "Tomei um banho quente e vesti o pijama de dinossauro",
    "Adoro lamber a colher de brigadeiro que sobra na panela",
    "A historinha de ninar do papai e a melhor de todas",
    "Fizemos uma guerra de travesseiros super divertida na sala",
    "Que delicia de chocolate quente em dia de chuva fria",
    "Brinquei de boneca e de carrinho com meus priminhos",
    "A aula de hoje foi muito gostosa de assistir e divertida",
    "Comi macarrao com queijo que estava uma delicia no jantar",
    "Dei um abraco apertado e um beijo na minha avo querida",
]

# ─────────────────────────────────────────────────────────────────────
# CLASSE: NEUTRO (adultos em contextos não sexuais/não ofensivos)
# ─────────────────────────────────────────────────────────────────────
dados_neutro = [
    # Esporte e entretenimento
    "Palmeiras nao tem mundial dizem os rivais na zoação",
    "Jogo de futebol emocionante ontem no estadio Maracana",
    "Comentario esportivo sobre o campeonato brasileiro de futebol",
    "Analise do desempenho do Flamengo no Brasileirao atual",
    "O time jogou bem mas perdeu nos penaltis ontem",
    "Corinthians venceu por dois a um no clasico paulista",
    "A seleção brasileira ganhou ouro nas olimpiadas",
    "Lance espetacular do Neymar driblando a defesa rival",
    "O basquete americano NBA tem jogadores altissimos",
    "Fui ao show de musica sertaneja no final de semana",
    "O album novo do artista ficou em primeiro no charts",
    "Assistindo serie de documentario sobre a Segunda Guerra",
    "Filme de acao com explosoes no cinema esse fim de semana",
    "Recomendo essa serie de suspense da Netflix incrivel",
    "Episodio novo da minha serie favorita de drama policial",
    "Podcast de historia que recomendo sobre o Imperio Romano",
    "Lendo romance literario de Gabriel Garcia Marquez",
    "Teatro municipal apresentou peca de Shakespeare famosa",
    "Stand up comedy do humorista foi muito engraçado",
    "Prefiro musica classica de Beethoven e Mozart",

    # Trabalho, tecnologia e cotidiano adulto
    "Conversa sobre trabalho e produtividade no home office",
    "Relatorio financeiro do trimestre com lucro aumentado",
    "Reuniao de equipe para discutir metas do proximo mes",
    "Amanha tem reuniao importante no escritorio central",
    "Preciso estudar para o vestibular de medicina este ano",
    "Meu celular novo chegou e a bateria dura o dia todo",
    "Preciso consertar o chuveiro que esta com pouca pressao",
    "O preço da gasolina subiu de novo esta semana",
    "Comecei a fazer academia essa semana para perder peso",
    "Trabalhando em um projeto novo de inteligencia artificial",
    "Reuniao com cliente importante para apresentar proposta",
    "O sistema caiu e perdi o relatorio que estava editando",
    "Instalei um software novo de edicao de video no PC",
    "Aprendi a usar o Excel avancado no curso de capacitacao",
    "Meu carro quebrou no meio da estrada ontem cedo",
    "Consertei a torneira da cozinha com ajuda do youtube",
    "Reformei o banheiro com ceramicas novas lindas",
    "Contratei uma faxineira para ajudar em casa quinzenalmente",
    "Paguei as contas do mes e sobrou pouco no saldo",
    "Comecei a poupar dinheiro para comprar um imovel",

    # Alimentação, saúde e vida adulta
    "Vou beber cafe quente pela manha antes do trabalho",
    "Leite de amendoas acabou na geladeira preciso comprar",
    "Receita de bolo de cenoura caseiro muito gostoso",
    "Vou ao medico fazer exame de rotina e check up geral",
    "Comecei dieta de proteina e corte de carboidratos",
    "Tomei antibiоtico para tratar a infeccao bacteriana",
    "Dormindo cedo para recuperar do estresse da semana",
    "Medico recomendou fazer caminhada diaria de trinta minutos",
    "Suco verde detox pela manha com espinafre e gengibre",
    "Preciso tomar vacina de gripe esse mes ainda",
    "Fiz check up completo e os exames deram todos normais",
    "Comecei terapia para cuidar da saude mental",
    "Pratico yoga toda manha para aliviar o estresse",
    "Estou tentando parar de fumar cigarros ha tres meses",
    "Minha pressão arterial estava alta precisei medicar",
    "Fiz cirurgia de apendicite de emergencia no hospital",
    "Alergico a amendoim e frutos do mar cuidado",
    "Vegetariano ha cinco anos por questoes de saude",
    "Excesso de açucar causa diabetes e problemas cardiacos",
    "Consulta com nutricionista para montar cardapio saudavel",

    # Noticias, politica e temas sociais (Informativos, não NSFW)
    "Discussao politica sobre economia e reforma tributaria",
    "Noticias do dia sobre o transito na cidade grande",
    "Debate no congresso nacional sobre nova lei fiscal",
    "O presidente assinou a nova lei hoje no congresso",
    "Mercado financeiro fechou em alta com a bolsa subindo",
    "Exploracao espacial com novo robo rover chegando em Marte",
    "Documentario sobre a historia da revolucao francesa",
    "Debate no STF sobre descriminalizacao e politicas publicas",
    "Noticia sobre violencia nas ruas e politica de segurança",
    "Educacao sexual preventiva nas escolas publicas do estado",
    "Aula de anatomia humana na faculdade de medicina hoje",
    "Casal foi visto jantando em restaurante elegante novo",
    "Pesquisa academica sobre comportamento humano e psicologia",
    "Analise sociologica da pobreza e desigualdade no Brasil",
    "Lançamento do novo album de musicas romanticas sertanejas",
    "Entrevista com especialista em politica internacional",
    "Evento cultural no centro historico da cidade",
    "Mensagem informativa sobre campanhas de vacinacao",
    "Relatorio sobre emissoes de carbono e aquecimento global",
    "Debate academico sobre inteligencia artificial e etica",

    # Viagem, lazer e vida social adulta
    "Postagem sobre viagem de ferias para a Europa",
    "As ferias estao chegando e planejamos ir a praia",
    "Hoje o por do sol estava muito lindo e colorido",
    "Plantei tomates e pimentoes na horta de casa",
    "Fomos jantar fora em familia no restaurante novo",
    "Aniversario de casamento de vinte anos celebrado",
    "Bebemos vinho tinto na janta com amigos adultos",
    "Cerveja gelada apos o trabalho com colegas",
    "Sairam para dançar forró no clube no sabado",
    "Festa de ano novo com amigos adultos na casa",
    "Casamento da minha prima foi muito bonito e elegante",
    "Churrasco de domingo com familia e amigos reunidos",
    "Viagem de mochilao para a America do Sul emocionante",
    "Hotel cinco estrelas em Salvador foi uma experiencia incrivel",
    "Trilha na mata atlantica com grupo de amigos aventureiros",
    "Corrida de rua de dez quilometros completada com sucesso",
    "Crossfit intenso e acabei completamente esgotado hoje",
    "Comprei ingresso para o show do meu artista favorito",
    "Fui ao bar assistir o jogo com os amigos ontem",
    "Alugamos um sitio para o feriado prolongado em familia",

    # ── HARD NEGATIVES v4.0 — conteúdo informativo/educativo sobre temas
    # sensíveis (NÃO é NSFW; menciona o tema, mas com finalidade legítima) ─
    "Documentario sobre o trafico de drogas e seus impactos sociais",
    "Reportagem sobre o combate a exploracao sexual de menores",
    "Palestra sobre educacao sexual e prevencao nas escolas publicas",
    "Aula de anatomia do corpo humano no curso de enfermagem",
    "Estudo academico sobre dependencia quimica e reabilitacao",
    "Materia jornalistica sobre violencia domestica e canais de denuncia",
    "Campanha de conscientizacao contra o abuso infantil nas redes",
    "Pesquisa sobre saude reprodutiva na faculdade de medicina",
    "Debate sobre a descriminalizacao das drogas no congresso nacional",
    "Livro sobre a historia da prostituicao na idade media europeia",
    "Curso de primeiros socorros ensina a lidar com casos de overdose",
    "Seminario sobre os efeitos do alcool no organismo humano",
    "Artigo cientifico sobre metodos contraceptivos modernos",
    "Reportagem sobre os riscos do cigarro e do tabagismo na saude",
    "Aula sobre o sistema reprodutor humano na biologia do ensino medio",

    # ── HARD NEGATIVES v4.0 — vida adulta legítima (vocabulário ambíguo) ─
    "Bebemos uma taca de vinho no jantar de aniversario de casamento",
    "Tomamos uma cerveja gelada com os amigos depois do trabalho",
    "Fomos a um bar tranquilo conversar sobre a vida adulta",
    "Casal comemorou as bodas de prata com uma viagem romantica",
    "Jantar a luz de velas para celebrar dez anos de namoro",
    "Aquele churrasco de domingo com a familia ficou delicioso",
    "Que prato gostoso esse risoto que pedimos no restaurante",
    "Comi uma feijoada deliciosa no almoco de sabado com amigos",
    "A massa ficou no ponto com um sabor gostoso de comida caseira",
    "Vou comer uma pizza enorme assistindo o jogo de futebol hoje",
    "Beijei minha esposa e fomos passear no parque de manha",
    "Te amo demais obrigado por mais um ano juntos meu amor",
    "Romance adulto de drama literario com personagens de quarenta anos",
    "Filme adulto no sentido de drama pesado nao recomendado a criancas",

    # ── HARD NEGATIVES v4.0 — cotidiano e humor com desabafo leve ───────
    "Que raiva perdi o onibus de novo nessa segunda feira",
    "Esse transito esta um caos absurdo hoje de manha cedo",
    "To morrendo de fome esperando o almoco ficar pronto logo",
    "Que dia cansativo so quero deitar e dormir agora cedo",
    "Mercado financeiro fechou em queda nesta sexta feira",
    "Nova lei de protecao de dados entra em vigor neste mes",

    # ── COTIDIANO CASUAL v4.0 — conversa do dia a dia em rede social ────
    # Representa o tipo de conteúdo majoritário numa rede social real, que
    # estava sub-representado no corpus e levava o modelo a tratar textos
    # casuais como fora de distribuição. Redigidos de forma distinta dos
    # textos da simulação para evitar vazamento de dados (data leakage).
    "Bom dia gente mais um dia de trabalho pela frente",
    "Acordei animado hoje o cafe da manha estava otimo",
    "Sexta feira chegou finalmente bora descansar o fim de semana",
    "O onibus atrasou muito hoje e cheguei tarde no servico",
    "Fiz um bolo de fuba caseiro pra tomar com cafe a tarde",
    "Meu cachorro derrubou o vaso de planta de novo na sala",
    "Acabei de chegar da academia treino puxado hoje cedo",
    "Domingo perfeito pra ficar em casa vendo serie na tv",
    "Comprei um celular novo a bateria dura o dia inteiro",
    "Choveu muito hoje e quase faltou luz no bairro inteiro",
    "Comecei a ler um livro otimo nao consigo largar mais",
    "Passei a tarde organizando o guarda roupa todo de novo",
    "Que preguica de segunda feira mas bora producir hoje",
    "Pedi comida no aplicativo e demorou quase uma hora",
    "Meu gato dormiu o dia todo em cima do sofa novo",
    "Fui na feira comprar frutas e verduras bem fresquinhas",
    "Plantei alface e cebolinha na horta da varanda de casa",
    "Trabalho de casa tem seus desafios mas economiza tempo",
    "Reuniao longa demais hoje podia ter sido um email rapido",
    "Terminei o relatorio do trabalho ainda bem ja era hora",
    "Lavei o carro de manha e a tarde ja estava sujo de novo",
    "A serie nova que comecei ontem ja viciei de vez nela",
    "Fiz panqueca no cafe da manha pra familia toda hoje",
    "Meu time joga hoje a noite torcida confiante na vitoria",
    "Comecei um curso online de design na parte da noite",
    "Que sol lindo hoje deu ate vontade de passear no parque",
    "Tomei um cafe otimo naquela cafeteria nova do centro",
    "Faxina geral no apartamento hoje com musica bem alta",
    "Comprei um presente de aniversario pro meu sobrinho querido",
    "Aprendi a fazer croche essa semana e nao consigo parar",
    "O dia foi corrido mas consegui terminar tudo no prazo",
    "Saudade da comida da minha mae nada se compara mesmo",
    "Fui ao mercado e esqueci justo o que eu mais precisava",
    "Maratonei a temporada nova no fim de semana inteirinho",
    "Acordei cedo pra ver o nascer do sol valeu muito a pena",
    "Meu filho deu os primeiros passos hoje chorei de emocao",
    "Consertei a torneira da cozinha sozinho assistindo tutorial",
    "Que delicia esse pao quentinho da padaria da esquina",
    "Hoje bateu aquela vontade de comer pizza assistindo filme",
    "Trabalhei demais essa semana mereco um descanso no domingo",
    "Comprei tinta nova vou pintar o quarto no fim de semana",
    "Reencontrei amigos antigos da escola foi muito bom rever",
    "Comecei a meditar dez minutos por dia e me sinto melhor",
    "O treino de hoje foi pesado mas sai me sentindo otimo",
    "Cafe da tarde com bolo de chocolate combinacao perfeita",
]

# ─────────────────────────────────────────────────────────────────────
# CLASSE: ADULTO (conteúdo inapropriado para menores — NSFW)
# ─────────────────────────────────────────────────────────────────────
dados_adulto = [
    # ── SEXUAL EXPLÍCITO DIRETO ──────────────────────────────────────
    "Conteudo sexual explicito pesado para adultos maiores",
    "Intimidade sexual intensa no quarto do motel",
    "Cena erotica do filme proibido para adultos",
    "Situacao sexual inadequada para criancas menores de dezoito",
    "Pornografia pesada na internet xvideos pornhub amadores",
    "Mulheres peladas nuas sem censura no site adulto onlyfans",
    "Vídeo porno amador vazado explicito adulto dezoito mais",
    "Cenas de sexo explicito no filme adulto sem censura",
    "Conteudo impróprio para menores de dezoito anos adulto",
    "Assunto sexual explicito conversas intimas proibidas",
    "Site de pornografia adulta com videos e fotos sem censura",
    "Gravação de ato sexual intimo casal amateur vazado",
    "Conteudo erótico impróprio para criança ou adolescente",
    "Transmissao ao vivo de ato sexual camgirl adulta",
    "Vídeos adultos classificação 18 mais conteudo erótico",
    "Conteúdo hentai animacao adulta proibida para menores",
    "Manga adulta erotica proibida para menores dezoito anos",

    # ── VOCABULÁRIO SEXUAL EXPLÍCITO E GÍRIAS ────────────────────────
    "Bater uma bronha gostosa sozinho escondido no banheiro",
    "Fazer sexo casual transar sem camisinha com desconhecidos",
    "Nudes quentes intimos exibicionismo mensagens privadas",
    "Chupar gozar trepar transar mamar motel suruba orgia",
    "Relação sexual ninfomaniaca tesão com estranhos",
    "Striptease acompanhante garota de programa boate adulta",
    "Orgia menage a trois apartamento putaria fetichista bdsm",
    "Prostitutas massagistas programa oferecendo servicos adultos",
    "Ejaculação gozo gozada na cara facial creampie porra",
    "Masturbação punheta siririca dedada bater uma",
    "Ejaculou dentro sem camisinha perigo de gravidez",
    "Sexo oral completo engolindo tudo sem preservativo",
    "Fetiche por calcinha usada sexo bizarro",
    "Pratica sexual sadomasoquismo dominacao submissao chicote",
    "Swing troca de casais evento privado adulto",
    "Voyeurismo espiar pessoas se trocando sem saber",
    "Sexo em local publico flagrante indecente",
    "Trair o namorado fazendo coisa feia escondido",
    "Corno satisfeito vendo esposa com outro homem",
    "Ato sexual filmado escondido sem consentimento",
    "Proxenetismo exploracao sexual comercial adulta",
    "Exibicionismo mostrar partes intimas em publico",
    "Sexting fotos intimas trocadas sem consentimento menores",

    # ── VOCABULÁRIO CHULO E PALAVRÕES SEXUAIS ────────────────────────
    "Puto da vida caralho porra merda vai se fuder tomar no cu",
    "Vadia arrombada viado corno viadinho sapatao boiola",
    "Boquete chupa rola boqueteiro mama rola mama piroca",
    "Rapariga quenga puta safada piranha biscate cachorra",
    "Gostosa pelada raba bunda peitos buceta xereca rachada",
    "Cu anus buraco rosquinha cacete rola pau pica pingolim",
    "Piroca grande dura ereto tesuda molhada gozando gemendo",
    "Filho da puta desgraçado arrombado merda vai pra puta",
    "Me chama de vadia gostosa enquanto faz gostoso",
    "Que cu gostoso delicioso senta devagar gemendo hein",
    "Peito grande caindo para fora decote safado olha so",
    "Calcinha molhada de tesao deu vontade mesmo",
    "Pau duro empinado querendo entrar logo rapido",
    "Gozei tres vezes seguidas foi ótimo demais",
    "Ela gemeu gostoso enquanto ele entrava devagar",
    "Fudeu gostoso a noite toda sem parar gemendo",
    "Acabou dentro que delicia tesão incrível",
    "Xoxota apertada molhada gostosa delicia minha gente",
    "Rabuda gostosa bunduda caindo fora da calcinha",
    "Piroca dura na mão batendo logo gostoso",

    # ── GROOMING / ALICIAMENTO ONLINE ───────────────────────────────
    "Vem aqui em casa bebe escondido dos seus pais pra gente brincar",
    "Me manda foto sem roupa peladinha nudes fotos agora",
    "Qual a cor da sua calcinha o que voce ta vestindo mostra",
    "Vou te foder toda ate voce chorar gostosa safadinha",
    "Voce é nova aqui nunca ficou com homem mais velho",
    "Nao conta pra ninguem nosso segredo tá só entre nos",
    "Voce é muito linda para a sua idade quer ser minha",
    "Posso ser seu namorado mais velho voce é tao madura",
    "Vem pra minha casa seus pais nao precisam saber nada",
    "Manda video se tocando para mim agora no privado",
    "Quero ver como voce eh por baixo me manda algo",
    "Voce me deixa louco de tesao tao novinha gostosa",
    "Manda pack pago bem em pix transferencia rapida",
    "Te pago para mandar fotos suas intimas novinha",
    "Posso te dar presente se mandar fotos intimas",
    "Que lindinha voce eh de quanto anos é esse corpinho",
    "Crianca gostosa que eu quero ver sem roupa logo",
    "Menor de idade no snap privado manda foto agora",
    "Voce parece mais velha manda foto sem blusa vai",
    "Saudade do teu corpinho gostoso me manda foto",

    # ── NUDES, PACKS E VAZAMENTOS ────────────────────────────────────
    "Pack vazado de famosa disponivel para download gratis",
    "Nudes da ex vazados no telegram grupo privado adulto",
    "Fotos intimas sem consentimento espalhadas na internet",
    "Compro pack de fotos intimas pago no pix rapido",
    "Vendo pack de fotos e videos adultos privados baratos",
    "Grupo telegram fotos vazadas famosas intimas adultas",
    "Fotos de nude vazadas da influencer famosa",
    "Pack gratuito nudes fotos videos adultos site piratas",
    "Me manda pack de pe nu rabuda agora no dm",
    "Vendendo meu pack intimo fotos e videos sensuais",
    "Venda de conteudo adulto onlyfans privacy privacy fans",

    # ── DROGAS PESADAS ───────────────────────────────────────────────
    "Fumar um beck baseado maconha prensado skunk erva haxixe",
    "Cheirar carreira de po branca neve cocaina teco tequinho tiro",
    "Droga sintetica ecstasy bala lsd lança perfume ácido MD MDMA",
    "Fentanil zumbi crack cachimbo pedrinha craqueiro vicio pesado",
    "Traficante biqueira boca de fumo aviãozinho vapor milicia",
    "Ketamina heroina opio morfina vicio heavy droga pesada",
    "Vendendo drogas na escola para criancas e adolescentes",
    "Usando drogas na balada rave com menores de idade",
    "Beber ate desmaiar coma alcoolico bebedeira extrema",
    "Cachaça a noite toda vomitar alcoolizado cirrose figado",
    "Combinando alcool com remedio controlado perigo de morte",
    "Snifando loló lança perfume num canto da festa",
    "Colando lanca perfume para ficar chapado na festa",
    "Chapado de maconha dirigindo carro a noite inteira",
    "Bebendo cachaça com menor de idade em casa escondido",
    "Oferecendo droga para adolescente na escola perigo",
    "Misturando bebida com calmante para ficar mais facil",

    # ── VIOLÊNCIA EXTREMA / GORE / AUTOMUTILAÇÃO ─────────────────────
    "Violencia esfaquear degolar matar decepar desmembrar arrancar",
    "Tortura mutilacao gore acidentes fatais suicidio depressao",
    "Automutilacao se cortar se machucar cortes no pulso",
    "Agressao fisica espancar pauladas surrar ate a morte homicidio",
    "Assassinato genocidio chacina execucao sangue armas tiro na cara",
    "Me machuquei de proposito pra sentir alguma coisa dor",
    "Pensando em me matar suicidio metodo facil como fazer",
    "Cortei meu braco de novo recaida automutilacao depressao",
    "Video de execucao ao vivo decapitacao gore pesado internet",
    "Imagens de tortura extorsao violencia extrema explicita",

    # ── LINGUAGEM OFENSIVA / DISCURSO DE ÓDIO ───────────────────────
    "Nordestino macaco preto segregação racismo odeio negros",
    "Judeu nojento conspiracao mundial antisemitismo nazismo",
    "Gay viado doenca mental vai se curar reparação terapia",
    "Mulher deveria ficar em casa calada fazer comida bunda",
    "Deficiente aleijado inutil pesa na sociedade improdutivo",
    "Gordo nojento lerdo inutil bola de sebo vergonha",
    "Matar todos os imigrantes varrer o lixo exterminar",
    "Estuprar a feminista que fica falando asneira imoral",

    # ── CONTEÚDO IMPLÍCITO / CAMUFLADO ──────────────────────────────
    "Beijo sensual pegação intensa balada saindo do controle",
    "Encontro para sexo sem compromisso putaria na festa",
    "Video viral nas redes sociais flagra casal adulto",
    "Tem mais de dezoito quer se divertir aqui comigo",
    "Vai ser gostoso voce vai gostar eu garanto querida",
    "Noite incrivel de prazer intenso no quarto com ela",
    "Ficamos na cama a noite toda sem dormir nada",
    "Amor de madrugada trepada boa no quarto obscuro",
    "Acabei fazendo coisa que nao devia com pessoa errada",
    "Pegamos geral na festa sem compromisso pura curtição",
    "Rolou coisa boa la escondido dos outros na festa",
    "Ficar com varias pessoas na mesma noite eh gostoso",
    "Convite para noite de prazer entre adultos consentidos",
    "Encontro intimo marcado hotel pago adiantado hoje",
    "Massagem sensual com final feliz disponivel agora",
    "Acompanhante de luxo discreta para eventos particulares",
    "Garota de programa experiente disponivel cidade inteira",
    "Programa para cavalheiros exigentes cidade grande hotel",

    # ── ASSÉDIO / BULLYING SEXUAL ────────────────────────────────────
    "Mandei a foto dela pelada para todo mundo ver haha",
    "Vou espalhar as fotos da ex safada por toda internet",
    "Ela merece apanhar manda foto intima dela eim",
    "Constrangendo a menina na escola por ter seios grandes",
    "Postei o video dela sem roupa ela ficou humilhada",
    "Ameaca de divulgar foto intima se nao ficar comigo",
    "Revenge porn postado para humilhar e destruir reputacao",
    "Chantagem sexual ameaçando vazar fotos de menor de idade",
    "Grupo no zap para humilhar menina com fotos dela",
    "Vazei as fotos da menina novinha que me rejeitou",
]

# ─────────────────────────────────────────────────────────────────────
# CONSTRUÇÃO DO DATAFRAME
# ─────────────────────────────────────────────────────────────────────
textos = dados_infantil + dados_neutro + dados_adulto
classes = (
    ["infantil"] * len(dados_infantil) +
    ["neutro"] * len(dados_neutro) +
    ["adulto"] * len(dados_adulto)
)

assert len(textos) == len(classes), f"Mismatch: {len(textos)} textos vs {len(classes)} classes"

df = pd.DataFrame({"texto": textos, "classe": classes})

# ═════════════════════════════════════════════════════════════════════
# ETAPA 1: PRÉ-PROCESSAMENTO
# ═════════════════════════════════════════════════════════════════════
df["texto_clean"] = df["texto"].apply(clean_text)
X = df["texto_clean"]
y = df["classe"]

# ═════════════════════════════════════════════════════════════════════
# ETAPA 2: PIPELINE DE MACHINE LEARNING (v4.0)
# ═════════════════════════════════════════════════════════════════════
# Mudanças da v4.0 em relação à v3.0, voltadas a REDUZIR FALSOS POSITIVOS
# sem comprometer a meta de Recall >= 85% para a classe adulta:
#   - ngram_range=(1,2): unigramas e bigramas. Trigramas (1,3) elevavam a
#     esparsidade e a memorização de sequências raras, sem ganho de recall.
#   - min_df=2: termos que aparecem em um único documento são descartados,
#     reduzindo a memorização de gatilhos raros e melhorando a precisão.
#   - class_weight=None: na v3.0 o peso adulto=2.0 enviesava o classificador
#     para "adulto" em textos curtos/sem sinal, gerando falsos positivos em
#     conteúdo cotidiano. Como a Camada 1 (regex) já assegura a sensibilidade
#     aos termos explícitos, o peso foi removido.
#   - O limiar de decisão deixou de ser fixo (0,35) e passa a ser CALIBRADO
#     por validação cruzada (Etapa 3), pelo menor valor cuja especificidade
#     out-of-fold seja >= 0,99 (controle direto da taxa de falsos positivos).
# ═════════════════════════════════════════════════════════════════════
pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=20000,
        sublinear_tf=True,
        min_df=2,
        analyzer='word',
        strip_accents='unicode'
    )),
    ("clf", LogisticRegression(
        # v4.0: class_weight=None. Na v3.0 o peso adulto=2.0 elevava o viés
        # do classificador para "adulto" em textos curtos/vazios de sinal,
        # gerando falsos positivos em conteúdo cotidiano. Como a Camada 1
        # (regex) já assegura a sensibilidade aos termos explícitos, o peso
        # foi removido para tornar a Camada 2 mais precisa.
        class_weight=None,
        max_iter=5000,
        C=2.0,
        solver='lbfgs'
    ))
])

def prever_com_limiar(pipe, textos, thr):
    """
    Predição multiclasse com limiar custom para a classe adulto. Abaixo do
    limiar, retorna a classe NÃO adulta mais provável (mesma regra da Camada 3
    em produção), de modo que o limiar seja a fronteira real de bloqueio.
    """
    proba = pipe.predict_proba(textos)
    cls = list(pipe.classes_)
    ia = cls.index("adulto")
    out = []
    for p in proba:
        if p[ia] >= thr:
            out.append("adulto")
        else:
            nao = [(p[i], c) for i, c in enumerate(cls) if c != "adulto"]
            out.append(max(nao)[1])
    return out


def treinar_e_salvar():
    """Executa CV, calibração de limiar, treino final e persistência."""
    from sklearn.base import clone
    from sklearn.metrics import recall_score, precision_score

    print(f"\n[DATASET] Configuracao do Treinamento v4.0")
    print(f"   Total de amostras: {len(df)}")
    print(f"   - Infantil: {len(dados_infantil)} amostras")
    print(f"   - Neutro:   {len(dados_neutro)} amostras")
    print(f"   - Adulto:   {len(dados_adulto)} amostras")

    # ── ETAPA 3: VALIDAÇÃO CRUZADA + CALIBRAÇÃO DO LIMIAR ──────────────
    kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    def recall_adulto(y_true, y_pred):
        return recall_score(y_true, y_pred, labels=["adulto"], average="macro", zero_division=0)

    cv_recall = cross_val_score(pipeline, X, y, cv=kf, scoring=make_scorer(recall_adulto))
    cv_f1 = cross_val_score(pipeline, X, y, cv=kf, scoring='f1_weighted')
    print(f"\n[CV] Validacao Cruzada (5-Fold) - decisao por argmax:")
    print(f"   Recall Adulto (CV):   {cv_recall.mean():.4f} (+/- {cv_recall.std()*2:.4f})")
    print(f"   F1-Score Ponderado:   {cv_f1.mean():.4f} (+/- {cv_f1.std()*2:.4f})")

    # Probabilidades out-of-fold (loop explícito, evitando o label-encoding
    # interno do cross_val_predict).
    X_arr, y_arr = X.values, y.values
    oof_padulto = np.zeros(len(y_arr))
    for tr_idx, te_idx in kf.split(X_arr, y_arr):
        m = clone(pipeline)
        m.fit(X_arr[tr_idx], y_arr[tr_idx])
        ia = list(m.classes_).index("adulto")
        oof_padulto[te_idx] = m.predict_proba(X_arr[te_idx])[:, ia]
    y_bin = (y_arr == "adulto").astype(int)

    # CALIBRAÇÃO ORIENTADA AO CONTROLE DA TAXA DE FALSOS POSITIVOS.
    # O corpus de treino é aproximadamente balanceado (~33% adulto), mas numa
    # rede social real o conteúdo adulto é minoritário. Um limiar calibrado por
    # precisão/F1 no conjunto balanceado fica sistematicamente baixo para o uso
    # real (prior-probability shift), reintroduzindo falsos positivos. Para
    # evitar isso de forma independente da prevalência, o limiar é o MENOR valor
    # cuja ESPECIFICIDADE out-of-fold (1 - FPR) seja >= ESPECIFICIDADE_ALVO.
    ESPECIFICIDADE_ALVO = 0.99
    neg_mask = (y_bin == 0)
    candidatos = []
    for thr in [i / 100 for i in range(5, 96)]:
        pred_bin = (oof_padulto >= thr).astype(int)
        espec = 1.0 - pred_bin[neg_mask].mean()
        rec = recall_score(y_bin, pred_bin, zero_division=0)
        prec = precision_score(y_bin, pred_bin, zero_division=0)
        candidatos.append((thr, espec, rec, prec))
    viaveis = [c for c in candidatos if c[1] >= ESPECIFICIDADE_ALVO]
    thr_adulto, espec_thr, rec_thr, prec_thr = (
        viaveis[0] if viaveis else max(candidatos, key=lambda c: c[1])
    )
    print(f"\n[CALIBRACAO] Limiar (menor com especificidade OOF >= {ESPECIFICIDADE_ALVO:.2f}): {thr_adulto:.2f}")
    print(f"   OOF @ limiar -> Especificidade: {espec_thr:.4f} | Recall: {rec_thr:.4f} | Precision: {prec_thr:.4f}")

    # ── ETAPA 4: TREINAMENTO FINAL (Split 80/20 estratificado) ─────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    pipeline.fit(X_train, y_train)
    y_pred = prever_com_limiar(pipeline, X_test, thr_adulto)

    print("\n" + "=" * 65)
    print(f"RELATORIO DE CLASSIFICACAO (TEST SET - 20%) @ limiar={thr_adulto:.2f}")
    print("=" * 65)
    print(classification_report(y_test, y_pred, digits=4, zero_division=0))
    cm = confusion_matrix(y_test, y_pred, labels=pipeline.classes_)
    print("MATRIZ DE CONFUSAO")
    print(f"   Classes (ordem): {list(pipeline.classes_)}")
    print(cm)

    # ── SALVAR MODELO E METADADOS ──────────────────────────────────────
    joblib.dump(pipeline, "pipeline.pkl")
    with open("pipeline_meta.json", "w", encoding="utf-8") as f:
        json.dump({
            "versao": "4.0",
            "modelo": "TfidfVectorizer(1,2) + LogisticRegression(class_weight=None, C=2.0)",
            "threshold_adulto": thr_adulto,
            "criterio_limiar": f"menor limiar com especificidade OOF >= {ESPECIFICIDADE_ALVO}",
            "cv_recall_adulto_argmax": float(cv_recall.mean()),
            "cv_recall_adulto_std": float(cv_recall.std()),
            "n_amostras": int(len(df)),
            "n_adulto": int((y == "adulto").sum()),
            "n_infantil": int((y == "infantil").sum()),
            "n_neutro": int((y == "neutro").sum()),
        }, f, ensure_ascii=False, indent=2)

    print(f"\n[DONE] Pipeline v4.0 salvo (limiar={thr_adulto:.2f} em pipeline_meta.json)")
    print(f"   Amostras treinadas: {len(X_train)} | Testadas: {len(X_test)} | Total: {len(df)}")


if __name__ == "__main__":
    treinar_e_salvar()
