"""
populate_db.py — Popula o banco do Conecta com dados realistas.

- 100 contas (idades variadas, adultos e menores)
- 400+ publicações escritas como pessoas reais escreveriam
- Curtidas, comentários, respostas, seguidores
- Trending alimentado com engajamento real
- Classificação feita pelo modelo de IA (não hardcoded)
"""

import sys, os, random
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Post, PostLike, Comment, CommentLike, Notification
from flask_bcrypt import Bcrypt
from ia.model_local import classificar_local

bcrypt = Bcrypt(app)
random.seed(42)

# ═══════════════════════════════════════════════════════════════════════
# DADOS DE USUÁRIOS (100 contas)
# ═══════════════════════════════════════════════════════════════════════

NOMES = [
    # Adultos (60)
    ("Lucas Oliveira", "lucas.oli", 24), ("Fernanda Costa", "fe.costa", 28),
    ("Rafael Mendes", "rafa.mendes", 31), ("Juliana Souza", "ju.souza", 26),
    ("Pedro Henrique", "pedroh", 33), ("Amanda Lima", "amanda.lima", 22),
    ("Thiago Santos", "thiago.s", 29), ("Camila Rocha", "camila.rocha", 27),
    ("Bruno Almeida", "bruno.alm", 35), ("Larissa Ferreira", "lari.fer", 23),
    ("Diego Nascimento", "diego.nasc", 30), ("Beatriz Cardoso", "bia.cardoso", 25),
    ("Matheus Ribeiro", "matt.ribeiro", 32), ("Isabela Martins", "isa.martins", 21),
    ("Gabriel Pereira", "gab.pereira", 28), ("Natalia Gomes", "nat.gomes", 26),
    ("Victor Hugo", "victorh", 34), ("Carolina Dias", "carol.dias", 24),
    ("Rodrigo Barros", "rod.barros", 29), ("Patricia Moreira", "pat.moreira", 31),
    ("Leonardo Castro", "leo.castro", 27), ("Aline Barbosa", "aline.barb", 23),
    ("Felipe Correia", "felipe.c", 36), ("Mariana Teixeira", "mari.teix", 25),
    ("Henrique Lopes", "henrique.l", 30), ("Raquel Nunes", "raquel.n", 22),
    ("Gustavo Ramos", "gus.ramos", 33), ("Daniela Freitas", "dani.freitas", 28),
    ("Andre Vieira", "andre.v", 26), ("Priscila Carvalho", "pri.carvalho", 24),
    ("Marcelo Araujo", "marcelo.a", 38), ("Vanessa Pinto", "vanessa.p", 27),
    ("Ricardo Azevedo", "ricardo.az", 31), ("Leticia Monteiro", "leti.mont", 23),
    ("Eduardo Campos", "edu.campos", 29), ("Sabrina Reis", "sabrina.r", 25),
    ("Caio Fernandes", "caio.fern", 22), ("Tatiane Melo", "tati.melo", 30),
    ("Vinicius Duarte", "vini.duarte", 34), ("Renata Siqueira", "renata.siq", 26),
    ("Joao Paulo", "jp.silva", 40), ("Sandra Machado", "sandra.m", 37),
    ("Anderson Borges", "anderson.b", 28), ("Cintia Nogueira", "cintia.nog", 24),
    ("Marcos Aurelio", "marcos.aur", 42), ("Fabiana Cunha", "fabi.cunha", 29),
    ("Leandro Pires", "leandro.p", 33), ("Monica Dantas", "monica.d", 26),
    ("Sergio Batista", "sergio.bat", 45), ("Adriana Moura", "adri.moura", 31),
    ("Wellington Cruz", "well.cruz", 27), ("Elaine Rosa", "elaine.rosa", 24),
    ("Cristiano Gomes", "cris.gomes", 35), ("Pamela Fonseca", "pamela.f", 22),
    ("Roberto Leal", "roberto.leal", 39), ("Simone Tavares", "simone.tav", 28),
    ("Alex Sandro", "alex.sandro", 25), ("Flavia Medeiros", "flavia.med", 30),
    ("Danilo Sampaio", "danilo.samp", 32), ("Bianca Aguiar", "bianca.ag", 23),

    # Adolescentes 14-17 (25)
    ("Miguel Teen", "miguel.t", 17), ("Sofia Adolescente", "sofia.teen", 16),
    ("Arthur Jovem", "arthur.jov", 15), ("Helena Studies", "helena.st", 17),
    ("Davi Estudante", "davi.est", 14), ("Laura Escola", "laura.esc", 16),
    ("Bernardo Gamer", "berna.gamer", 15), ("Valentina Star", "val.star", 17),
    ("Samuel Esporte", "samuel.esp", 16), ("Alice Leitora", "alice.leit", 14),
    ("Nicolas Skate", "nico.skate", 15), ("Manuela Arte", "manu.arte", 16),
    ("Lorenzo Music", "lorenzo.m", 17), ("Cecilia Dance", "ceci.dance", 14),
    ("Enzo Gabriel", "enzo.gab", 15), ("Luana Stars", "luana.stars", 16),
    ("Theo Games", "theo.games", 17), ("Isadora Blog", "isa.blog", 15),
    ("Heitor Fut", "heitor.fut", 14), ("Giovanna Art", "gio.art", 16),
    ("Pietro Nerd", "pietro.nerd", 15), ("Maria Clara", "mc.silva", 17),
    ("Lucca Santos", "lucca.sant", 16), ("Antonella Costa", "anto.costa", 14),
    ("Benjamin Tech", "ben.tech", 15),

    # Crianças 8-13 (15)
    ("Pedrinho Kids", "pedrinho.k", 12), ("Mariazinha Fofa", "mariazinha", 10),
    ("Joaozinho Escola", "joaozinho.e", 11), ("Ana Luiza Kid", "analuiza.k", 9),
    ("Lucasinho Game", "lucasinho", 13), ("Sophia Play", "sophia.play", 10),
    ("Enzo Pequeno", "enzo.peq", 8), ("Valentina Kid", "val.kid", 11),
    ("Theo Crianca", "theo.kid", 9), ("Helena Mini", "helena.mini", 12),
    ("Arthur Play", "arthur.play", 10), ("Laura Mini", "laura.mini", 13),
    ("Gabriel Kid", "gab.kid", 11), ("Isabella Play", "isa.play", 8),
    ("Rafael Junior", "rafa.jr", 12),
]

# ═══════════════════════════════════════════════════════════════════════
# PUBLICAÇÕES REALISTAS (400+)
# Escritas como pessoas reais — o modelo classifica automaticamente.
# ═══════════════════════════════════════════════════════════════════════

# --- Posts do dia a dia (adultos) ---
POSTS_COTIDIANO = [
    "Bom dia pessoal! Mais uma segunda-feira chegou, bora trabalhar",
    "Café pronto, playlist boa e home office. Vida que segue",
    "Alguém mais acordou com essa chuva maravilhosa hoje?",
    "Fiz pão de queijo caseiro e ficou divino, receita da vó",
    "Trânsito impossível hoje, 2 horas pra chegar no trabalho",
    "Finalmente sexta-feira!! Quem mais tava precisando?",
    "Pedido do iFood atrasou 40 minutos, tô morrendo de fome",
    "Achei uma cafeteria incrível aqui no centro, café nota 10",
    "Voltando da academia, treino de perna pesadão hoje",
    "Cozinhei um risoto de cogumelos pela primeira vez, ficou bom demais",
    "Meu cachorro destruiu mais um chinelo, já é o quinto esse mês",
    "Assistindo série nova na Netflix, tô viciada já",
    "Reunião de 3 horas que podia ter sido um email",
    "Fiz bolo de cenoura com cobertura de chocolate, quem quer?",
    "Domingo de churrasco com a família, dia perfeito",
    "Meu gato dormiu em cima do meu notebook de novo",
    "Comprando presente de aniversário pro meu sobrinho",
    "Que pôr do sol incrível hoje, tirei foto da varanda",
    "Maratonei 3 temporadas de Breaking Bad no fim de semana",
    "Almoço de domingo na casa da sogra, comida caseira é outra coisa",
    "Preciso trocar meu celular, esse aqui tá travando muito",
    "Fiz unha e cabelo hoje, autoestima lá em cima",
    "Voltei a ler livros físicos, tela cansa demais os olhos",
    "Organizei meu guarda-roupa inteiro hoje, achei roupa de 2018",
    "Meu vizinho tá com obra há 3 meses, não aguento mais barulho",
    "Testei receita nova de cookie, ficou crocante por fora e macio por dentro",
    "Lavei o carro inteiro e 5 minutos depois choveu",
    "Comecei a fazer crochê, viciante demais",
    "Plantei tomate na varanda e tá crescendo, muito feliz",
    "Minha mãe mandou aquele tupper de comida, saudade de casa",
    "Dia de faxina geral no apartamento, coloquei música alta",
    "Provei açaí pela primeira vez na vida e amei",
    "Perdi o ônibus por 10 segundos, que raiva",
    "Fiz uma torta de limão incrível pro almoço de família",
    "Comprei um livro novo na feira, mal posso esperar pra ler",
    "Chuva forte aqui, espero que não falte luz de novo",
    "Meu filho deu os primeiros passos hoje, chorei de emoção",
    "Tentei fazer sushi em casa, ficou feio mas gostoso",
    "Assistindo jogo do Brasil com a galera, vamo que vamo",
    "Meu notebook finalmente chegou, 15 dias de espera",
]

# --- Posts sobre trabalho/carreira ---
POSTS_TRABALHO = [
    "Entrega de projeto amanhã, tô aqui desde as 7 da manhã",
    "Passei na entrevista de emprego, começo segunda que vem!",
    "Freelancer é bom mas essa instabilidade financeira complica",
    "Recebi uma proposta de emprego muito boa, tô pensando em aceitar",
    "Dia de apresentação pro cliente, nervoso demais",
    "Finalmente consegui a promoção que eu queria há 2 anos",
    "Trabalhando com Python há 3 anos e cada dia aprendo algo novo",
    "Começando um curso de design UX essa semana, animada",
    "Meu chefe pediu pra refazer o relatório inteiro, de novo",
    "Networking é tudo, conheci gente incrível nesse evento",
    "Home office tem seus prós e contras né, falta interação",
    "Certificação AWS conquistada! Muito orgulho",
    "Estágio confirmado na empresa dos sonhos, gratidão",
    "Deadline apertado mas a equipe tá dando conta, time foda",
    "Fiz minha primeira venda como MEI hoje, emocionante",
    "Aprendi React em 2 meses, agora partiu Next.js",
    "Burnout é real, galera. Cuidem da saúde mental de vocês",
    "Evento de tecnologia amanhã, alguém mais vai?",
    "Acabei meu TCC finalmente, sensação de alívio indescritível",
    "Primeiro dia no emprego novo, muito ansioso mas feliz",
]

# --- Posts de esporte/lazer ---
POSTS_ESPORTE = [
    "Corrida matinal de 5km, melhor forma de começar o dia",
    "Jogo do Flamengo hoje, tô confiante na vitória",
    "Comecei a jogar tênis, mais difícil do que parece",
    "Fui fazer trilha no fim de semana, paisagem incrível",
    "Gol de bicicleta do Neymar foi absurdo, genial",
    "Natação é o melhor exercício que existe, não tem discussão",
    "Maratona marcada pro mês que vem, treinando todo dia",
    "Jogo de vôlei com os amigos da faculdade, saudade disso",
    "UFC ontem foi insano, que nocaute no último round",
    "Comecei yoga essa semana, minha flexibilidade é zero",
    "Pelada de quarta-feira com a galera do trabalho, ganhamo",
    "Campeonato de futsal da firma, nosso time tá invicto",
    "Surfei pela primeira vez, tomei muito caldo mas valeu",
    "Crossfit tá acabando comigo mas os resultados aparecem",
    "Final do campeonato brasileiro vai ser eletrizante esse ano",
    "Voltei a pedalar depois de anos, joelhos reclamando",
    "Jogo de basquete com os primos domingo, revanche marcada",
    "Fiz meu primeiro 10km sem parar, meta alcançada",
    "Futebol society toda terça, melhor terapia que existe",
    "Assistindo Olimpíadas, Brasil tá arrasando na ginástica",
]

# --- Posts de tecnologia/games ---
POSTS_TECH = [
    "Comprei o PS5 finalmente, alguém tem dica de jogo?",
    "ChatGPT tá mudando tudo, inteligência artificial é o futuro",
    "Montei meu PC gamer, RTX 4060 rodando tudo no ultra",
    "Novo iPhone saiu e eu aqui feliz com meu Android de 2022",
    "Joguei Zelda por 12 horas seguidas, não me arrependo",
    "Atualizei o Windows e meu PC ficou mais lento, clássico",
    "Programando em Python é quase como escrever em português",
    "Minecraft com mods é outro jogo completamente diferente",
    "Linux é superior pra desenvolvimento, não tem discussão",
    "Meu Wi-Fi caiu bem na hora da ranked, perdi a partida",
    "Fiz um site completo em uma semana usando Flask, orgulho",
    "GTA 6 vai ser insano pelo que mostraram no trailer",
    "Comprei um Kindle e não consigo largar, leio todo dia",
    "Raspberry Pi é o brinquedo mais legal que um programador pode ter",
    "Comecei a estudar machine learning, fascinante esse mundo",
    "Formatei o PC e esqueci de fazer backup das fotos, que dor",
    "Arduino controlando as luzes da minha casa, automação top",
    "Rank Diamante no League of Legends finalmente, 500 horas",
    "Podcast sobre tecnologia é meu companheiro no trânsito",
    "Impressora 3D chegou, primeira coisa que imprimi foi um vaso",
]

# --- Posts de estudantes/escola ---
POSTS_ESTUDANTE = [
    "Prova de matemática amanhã e eu não estudei nada ainda",
    "Trabalho em grupo é sempre a mesma coisa, só eu faço",
    "Passei de ano com média 8, orgulho de mim mesmo",
    "Feira de ciências da escola, nosso projeto ficou top",
    "Professor de história conta as melhores histórias",
    "Cantina da escola tá vendendo coxinha nova, deliciosa",
    "Simulado do ENEM foi difícil demais, redação complicada",
    "Formatura do ensino médio mês que vem, ansiosa demais",
    "Biblioteca da escola tem livros incríveis que ninguém lê",
    "Excursão pro museu de ciências semana que vem, mal posso esperar",
    "Aula de educação física hoje, jogamos queimada",
    "Ganhei medalha na olimpíada de matemática da escola",
    "Estudando pro vestibular todo dia, cansativo mas necessário",
    "Intervalo da escola é a melhor hora do dia",
    "Apresentação de trabalho amanhã, ensaiando o dia inteiro",
    "Comecei curso de inglês, tô no nível básico ainda",
    "Aula de laboratório de química, fizemos vulcão de bicarbonato",
    "Festival de talentos da escola, vou cantar com minha banda",
    "Nota 10 na redação, a professora elogiou meu texto",
    "Último ano do ensino médio, bateu uma nostalgia",
    "Estudando biologia celular, mitocôndria é a powerhouse da célula",
    "Aula de robótica na escola, montamos um robô seguidor de linha",
    "Passei no vestibular da federal, não acredito ainda",
    "Aula de artes hoje, pintamos telas com tinta acrílica",
    "Prova de português sobre Machado de Assis, li Dom Casmurro inteiro",
]

# --- Posts de crianças ---
POSTS_CRIANCA = [
    "Minha mãe fez bolo de chocolate pro meu aniversário!",
    "Joguei Roblox com meu amigo da escola a tarde toda",
    "Assisti Homem-Aranha com meu pai no cinema, muito legal",
    "Meu cachorrinho Rex aprendeu a dar a patinha hoje",
    "Ganhei um livro de dinossauros da minha avó, amei",
    "Fiz uma torre de Lego gigante que quase chegou no teto",
    "Aula de natação foi divertida, já sei nadar sozinho",
    "Desenhei minha família inteira no caderno de artes",
    "Brincamos de esconde-esconde no recreio, eu ganhei",
    "Meu hamster tá gordinho porque come demais, que fofo",
    "Aprendi a andar de bicicleta sem rodinha, caí só duas vezes",
    "Assisti Encanto da Disney pela terceira vez, nunca canso",
    "Plantamos feijão no algodão na escola, tá crescendo",
    "Minha professora é a melhor do mundo, ela é muito legal",
    "Ganhei figurinha brilhante rara no álbum de futebol",
    "Brinquei de massinha e fiz um dinossauro roxo",
    "Papai me levou no parque e andei na roda gigante",
    "Fiz um avião de papel que voou super longe na escola",
    "Comi pizza de calabresa no aniversário do meu amigo",
    "Meu irmãozinho nasceu hoje, agora sou irmão mais velho!",
    "Assistindo desenho do Gato de Botas, muito engraçado",
    "Brincamos de caça ao tesouro no quintal da vovó",
    "Ganhei uma medalha por ler 10 livros na biblioteca",
    "Minha tartaruga se chama Flash, mas ela é super lenta",
    "Fizemos uma cabana de lençol na sala e dormimos nela",
    "A gente fez sorvete de morango caseiro, ficou delicioso",
    "Joguei futebol no campinho e fiz dois gols, sou craque",
    "Colecionando pedras bonitas que acho no parque",
    "Minha mãe me ensinou a fazer panqueca, fiz sozinho!",
    "Assisti show de mágica na escola, o coelho sumiu de verdade",
]

# --- Posts de opinião/reflexão ---
POSTS_OPINIAO = [
    "Acho que as pessoas precisam ser mais gentis umas com as outras",
    "Saúde mental deveria ser prioridade em todo lugar de trabalho",
    "Livros mudam vidas, leiam mais e rolem menos o feed",
    "Gratidão por mais um dia, a vida é curta demais pra reclamar",
    "Educação é o caminho, não tem atalho pra um país melhor",
    "Nem toda opinião merece ser debatida, algumas merecem ser ignoradas",
    "Gentileza gera gentileza, simples assim",
    "Precisamos falar mais sobre ansiedade entre jovens",
    "Desconectar das redes de vez em quando faz bem demais",
    "A natureza é perfeita, precisamos cuidar melhor do planeta",
    "Quem lê mais tem mais empatia, tem pesquisa comprovando",
    "Todo mundo deveria aprender a cozinhar pelo menos o básico",
    "Música é terapia, coloquem seus fones e relaxem",
    "Paciência é uma virtude que pouca gente tem hoje em dia",
    "Às vezes a gente precisa parar e agradecer o que tem",
    "Respeitar o próximo custa zero reais",
    "Autoconhecimento é a jornada mais importante da vida",
    "Menos reclamação e mais ação, é assim que se muda as coisas",
    "Empatia é se colocar no lugar do outro de verdade",
    "A vida é feita de momentos simples, aproveitem cada um",
]

# --- Posts de humor ---
POSTS_HUMOR = [
    "Acordo cedo pra ir na academia, durmo cedo pra acordar cedo. Resultado: não vou na academia",
    "Meu nível de preguiça: levantei pra pegar o controle que tava no sofá do lado",
    "Segunda-feira deveria ser opcional, quem concorda curte aqui",
    "Eu no espelho: modelo. Eu na câmera frontal: senhor dos anéis",
    "Abri a geladeira 47 vezes e a comida continua a mesma",
    "Meu saldo bancário é uma comédia de terror",
    "Fiz dieta o dia inteiro e me pesei... engordei. Obrigado universo",
    "O Wi-Fi caiu e eu me tornei um ser humano produtivo por 5 minutos",
    "Comprei uma air fryer e agora sou chef de cozinha internacional",
    "Meu alarme das 6h: toca. Eu: mais 5 minutos. Resultado: 11h",
    "Pedi comida saudável no delivery e veio uma coxinha de brinde. Sinal do universo",
    "Falei que ia dormir cedo e cá estou às 3 da manhã vendo meme",
    "Adultar é basicamente resolver um problema atrás do outro",
    "Meu cachorro me olha como se eu fosse a pessoa mais incrível do mundo e eu agradeço",
    "Tentei fazer exercício em casa, o sofá venceu em 3 minutos",
    "Café é meu grupo sanguíneo nesse ponto",
    "Fiz uma planilha de gastos e me arrependi de ter olhado",
    "Semana tem 7 dias e eu tô cansado em todos eles",
    "Todo mundo postando viagem e eu aqui postando o almoço de marmita",
    "Meu celular caiu na privada. De novo. Preciso de uma capa subaquática",
]

# --- Posts de viagem/cultura ---
POSTS_VIAGEM = [
    "Fim de semana em Paraty, cidade mais linda do Rio",
    "Conheci Gramado no inverno, chocolate quente e fondue todo dia",
    "Praia de Jericoacoara é um paraíso, água cristalina demais",
    "Primeira viagem internacional pra Buenos Aires, amei a cultura",
    "Chapada dos Veadeiros é mágica, cachoeiras incríveis",
    "Salvador tem a melhor comida do Brasil, acarajé divino",
    "Fui pra Bonito e mergulhei com peixes em água transparente",
    "Serra Gaúcha no outono, as vinícolas são espetaculares",
    "Ouro Preto tem uma história incrível em cada esquina",
    "Manaus e a floresta amazônica, experiência de vida",
    "Foz do Iguaçu me deixou sem palavras, as cataratas são surreais",
    "Lençóis Maranhenses parece outro planeta, paisagem única",
    "Blumenau na Oktoberfest, cerveja artesanal de primeira",
    "Fernando de Noronha é o lugar mais bonito que já vi na vida",
    "Caminhada no Pico da Bandeira, vista do topo compensou tudo",
    "Recife tem praias urbanas incríveis, Porto de Galinhas é perfeita",
    "Museu do Amanhã no Rio é imperdível, arquitetura sensacional",
    "Arraial do Cabo, o Caribe brasileiro, água azul turquesa",
    "Inhotim em Minas é o maior museu a céu aberto da América Latina",
    "Pantanal é vida selvagem pura, vi onça pintada de perto",
]

# --- Posts de relacionamento (normais) ---
POSTS_RELACIONAMENTO = [
    "3 anos de namoro hoje, te amo demais meu amor",
    "Jantar surpresa pro aniversário da minha esposa, ficou emocionada",
    "Meu marido fez café da manhã na cama, casem com quem cozinha",
    "Passeio no parque com a namorada, dia perfeito e simples",
    "Melhor presente é tempo juntos, não precisa de nada caro",
    "Pedido de casamento aceito!! Ela disse sim!!",
    "15 anos de casados e ainda rimos juntos todo dia",
    "Primeiro encontro foi num café simples e até hoje é nosso lugar",
    "Saudade bate forte quando ela viaja a trabalho",
    "Fizemos aula de dança juntos, pisamos muito no pé um do outro",
    "Cozinhamos juntos todo domingo, nosso ritual favorito",
    "Carta de amor escrita à mão ainda é o melhor presente",
    "Meu namorado me surpreendeu com ingressos pro show que eu queria",
    "Casal que treina junto permanece junto, academia a dois",
    "Assistimos o pôr do sol na praia, momento mágico",
    "Bodas de madeira, 5 anos de muito amor e parceria",
    "Ela me conhece melhor do que eu mesmo, isso é amor",
    "Road trip com meu amor, 1000km de estrada e muita risada",
    "Jantar à luz de velas em casa, não precisa de restaurante caro",
    "Gratidão por ter alguém que me apoia em tudo na vida",
]

# --- Posts de música/arte ---
POSTS_MUSICA = [
    "Show do Coldplay foi a melhor experiência da minha vida",
    "Aprendendo a tocar violão, dedos doendo mas não desisto",
    "Playlist de MPB pra domingo chuvoso é obrigatório",
    "Fui no museu de arte moderna, exposição incrível",
    "Tim Maia é atemporal, que vozeirão absurdo",
    "Comecei a pintar quadros, terapia pura",
    "Festival de jazz esse fim de semana, quem vai?",
    "Samba de raiz no bar da esquina, noite perfeita",
    "Beethoven no fone de ouvido enquanto programo, produtividade máxima",
    "Teatro municipal tá com peça nova, ingressos esgotando",
    "Comprando vinil antigo na feira, coleção crescendo",
    "Fotografia de rua é meu hobby favorito, SP tem cenários incríveis",
    "Aula de piano começando essa semana, realizando um sonho",
    "Poesia de Carlos Drummond nunca envelhece",
    "Desenhando no iPad todo dia, evolução tá visível",
    "Rap nacional tem letras muito profundas, cultura riquíssima",
    "Exposição de Van Gogh em São Paulo, imperdível",
    "Tocando bateria na garagem, vizinhos amam (sqn)",
    "Cinema nacional tá produzindo filmes incríveis ultimamente",
    "Clube do livro toda segunda, lendo Clarice Lispector agora",
]

# --- Posts que testam o modelo (conteúdo adulto real de rede social) ---
POSTS_ADULTO_REALISTA = [
    "Ontem na festa rolou muita putaria, galera sem noção",
    "Manda nudes no privado que eu respondo rapidinho",
    "Esse cara é um filho da puta, não aguento mais",
    "Tô com um tesão absurdo, quem quer sair hoje?",
    "Fumei um beck ontem e fiquei chapado o dia inteiro",
    "Vídeo pornô desse ator é muito bom, alguém conhece?",
    "Vou te comer todinha quando a gente se encontrar",
    "Esse vagabundo me deve dinheiro há meses, desgraçado",
    "Festa no motel sexta, quem tá dentro? Bora putaria",
    "Maconha boa chegou, quem quiser é só chamar no dm",
    "Que buceta gostosa, manda mais fotos assim",
    "Suruba no sábado, quem anima? Chama no privado",
    "Cachorro desse arrombado cagou no meu jardim de novo",
    "Cocaína tá cara demais ultimamente, tráfico tá osso",
    "Que porra é essa? Vsf mano, vai tomar no cu",
    "Estou de saco cheio desse merda do meu chefe, fdp",
    "Boquete da namorada ontem foi surreal demais cara",
    "Quero trepar a noite inteira sem parar",
    "Fumando um baseado e assistindo filme, paz",
    "Pack de nudes disponível, chama no privado gente",
    "Essa gostosa tava rebolando na festa ontem, que delícia",
    "Punheta todo dia tá virando rotina, preciso de alguém",
    "Vou te foder tanto que tu vai esquecer teu nome",
    "Pegação generalizada na balada ontem, beijei umas 5",
    "Quem quiser trocar nude chama inbox, só maiores",
    "Essa mina é muito safada, adoro esse tipo",
    "Orgia no apart hotel semana que vem, fechado?",
    "Comprei ecstasy pro festival, vai ser insano",
    "Crack tá destruindo a cidade, cada dia mais gente na rua",
    "Stripper do cabaré ontem dançou muito, que show",
]

# --- Posts ambíguos (testam falsos positivos) ---
POSTS_AMBIGUOS = [
    "Aula de biologia sobre reprodução humana, muito interessante",
    "Livro sobre anatomia chegou, estudando pro vestibular de medicina",
    "Documentário sobre tráfico de drogas na Netflix, assustador",
    "Matéria sobre violência contra a mulher no jornal, revoltante",
    "Palestra sobre educação sexual na escola foi muito boa e necessária",
    "Pesquisa sobre dependência química pra faculdade de psicologia",
    "Reportagem sobre prostituição infantil, precisamos combater isso",
    "Filme adulto no sentido de drama pesado, não é pra criança",
    "Aula de educação sexual é importante pra adolescentes",
    "Estudo sobre drogas lícitas e ilícitas na faculdade de farmácia",
    "Romance adulto literário, protagonista tem 40 anos, ótima história",
    "Bebemos vinho no jantar romântico, noite especial",
    "Aula de anatomia no curso de enfermagem, corpo humano é fascinante",
    "Saímos pra dançar forró, transpirei muito mas foi divertido",
    "Massagem relaxante no spa, melhor investimento do mês",
    "Casal no parque se beijando, que cena fofa de se ver",
    "Livro sobre crimes reais que li é perturbador mas bem escrito",
    "Documentário sobre cartéis mexicanos, realidade assustadora",
    "Conversa sobre consentimento é fundamental nas escolas",
    "Estudando psicologia forense, casos de abuso são complexos",
]

# --- Posts de adolescentes ---
POSTS_ADOLESCENTE = [
    "Prova de física amanhã e eu não entendo nada de termodinâmica",
    "Crush olhou pra mim no corredor, dia feito",
    "TikTok me fez perder 3 horas de estudo, preciso de foco",
    "Minha mãe não deixa eu ir na festa, que injustiça",
    "Playlist de estudo no Spotify, lofi hip hop é vida",
    "Joguei Valorant até 2 da manhã, amanhã vou sofrer na escola",
    "Cabelo novo, autoestima renovada, aceitando elogios",
    "Amizade de verdade é rara, valorizo muito meus amigos",
    "Queria ter 18 logo pra poder dirigir, cansado de pegar ônibus",
    "Série nova do anime tá incrível, One Piece nunca decepciona",
    "Comecei a desenhar mangá, tô praticando todo dia",
    "Meu time ganhou o campeonato da escola, gol decisivo foi meu",
    "Drama na escola de novo, gente fofoqueira demais",
    "Estudando pro ENEM com vídeo aula, professor é muito bom",
    "Festa junina da escola, dancei quadrilha e comi muito paçoca",
    "Meus pais não entendem que YouTube é uma profissão de verdade",
    "Comprei meu primeiro tênis com meu dinheiro, orgulho",
    "K-pop dominou minha playlist inteira, não me julguem",
    "Dormindo na casa do melhor amigo, maratona de filme de terror",
    "Ansiedade pra vestibular tá batendo forte, respirando fundo",
    "Participei de grêmio estudantil pela primeira vez, experiência top",
    "Professor de filosofia faz a gente pensar em coisas que nunca pensei",
    "Simulado deu 680 pontos, meta é 750 pro ENEM",
    "Formatura chegando e eu nem sei o que vestir",
    "Aprendi a fazer ovo mexido perfeito, já sou adulto funcional",
]

# --- Posts extras cotidiano (mais volume) ---
POSTS_EXTRA_1 = [
    "Hoje é dia de feira, frutas fresquinhas e baratas",
    "Meu filho aprendeu a amarrar o tênis sozinho, marco importante",
    "Médico disse que meus exames estão ótimos, alívio total",
    "Inaugurou uma padaria artesanal aqui perto, pão delicioso",
    "Cortei o cabelo curto pela primeira vez, amei a mudança",
    "Vizinha trouxe um pedaço de bolo, gente boa existe",
    "Fiz matrícula na auto escola, nervoso pra primeira aula",
    "Meu avô completou 80 anos hoje, festa linda em família",
    "Comprando material escolar pro meu filho, lista enorme",
    "Choveu granizo aqui, nunca vi pedras de gelo tão grandes",
    "Meu cachorro aprendeu a sentar, treinamento tá funcionando",
    "Recebi encomenda que pedi há 20 dias, finalmente chegou",
    "Acordei 5h da manhã pra ver o nascer do sol, valeu a pena",
    "Minha filha cantou no coral da escola, chorei de emoção",
    "Fiz brigadeiro pra vender na feira da igreja, vendeu tudo",
    "Troquei a lâmpada da sala sozinho pela primeira vez",
    "Meu carro passou na vistoria de primeira, milagre",
    "Domingo de chuva é pedir pizza e assistir filme em casa",
    "Comecei a caminhada diária no parque, 30 minutos por dia",
    "Ganhei um vaso de suculenta de presente, decorando a estante",
]

# --- Posts extras de saúde/bem-estar ---
POSTS_EXTRA_2 = [
    "Voltei a terapia depois de 2 anos, melhor decisão",
    "Meditação de 10 minutos por dia mudou minha rotina",
    "Dormir 8 horas faz toda diferença no dia seguinte",
    "Comecei a beber 2 litros de água por dia, pele melhorou",
    "Alongamento toda manhã, minhas costas agradecem",
    "Dentista disse que não tenho cárie, primeira vez em anos",
    "Reduzi o açúcar da dieta e já sinto diferença na energia",
    "Corrida leve de 20 minutos alivia todo o estresse do dia",
    "Fiz check-up completo, prevenção é o melhor remédio",
    "Ioga antes de dormir ajuda demais na qualidade do sono",
    "Parei de tomar refrigerante, primeiro mês sem e tô bem",
    "Caminhada na natureza é o melhor remédio pra ansiedade",
    "Nutricionista montou um cardápio incrível pra mim",
    "Receita de suco verde que realmente fica gostoso, descobri",
    "Fisioterapia tá resolvendo minha dor no ombro, aliviado",
    "Pilates duas vezes por semana, postura melhorou demais",
    "Aprendi que descansar não é preguiça, é necessidade",
    "Chá de camomila antes de dormir virou meu ritual",
    "Meu exame de sangue veio perfeito, dieta tá funcionando",
    "Banho quente depois de um dia cansativo é terapêutico",
]

# --- Posts extras de comida/receitas ---
POSTS_EXTRA_3 = [
    "Fiz strogonoff de frango pela primeira vez, família amou",
    "Bolo de fubá com café, combinação perfeita da tarde",
    "Receita de panqueca fit com banana e aveia, saudável e boa",
    "Experimentei comida japonesa pela primeira vez, sashimi é incrível",
    "Minha lasanha ficou melhor que de restaurante, modéstia zero",
    "Caldo verde no frio é abraço em forma de comida",
    "Aprendi a fazer pão caseiro na pandemia e nunca mais parei",
    "Açaí com granola e banana é meu lanche da tarde perfeito",
    "Feijoada de sábado com laranja e couve, tradição que amo",
    "Torta de frango com massa podre, receita da minha mãe",
    "Café coado no filtro de pano é incomparável, sabor único",
    "Sorvete caseiro de manga que fiz ficou melhor que de sorveteria",
    "Tapioca com queijo coalho e mel, café da manhã nordestino",
    "Moqueca baiana feita em casa, cheiro tomou conta do prédio",
    "Pipoca com manteiga assistindo filme, programa perfeito",
    "Bolo de milho da festa junina é o melhor bolo que existe",
    "Coxinha crocante por fora e cremosa por dentro, perfeição",
    "Vitamina de abacate com leite condensado da minha avó",
    "Arroz, feijão, bife e salada. Simples e perfeito",
    "Pastel de feira com caldo de cana, não tem coisa melhor",
]

# --- Posts extras de pets ---
POSTS_EXTRA_4 = [
    "Adotei um gatinho do abrigo, já dominou a casa inteira",
    "Meu cachorro late pra própria sombra, corajoso demais",
    "Levei meu dog no petshop e ele voltou cheiroso e estiloso",
    "Minha gata dorme 18 horas por dia, vida boa é assim",
    "Passeio no parque com os cachorros, eles adoram correr",
    "Meu papagaio aprendeu a imitar o barulho do micro-ondas",
    "Hamster correndo na rodinha às 3 da manhã, barulho danado",
    "Adotamos um vira-lata caramelo e ele é o rei da casa",
    "Meu gato derrubou o vaso de planta pela quinta vez esse mês",
    "Cachorro no veterinário tomou vacina e ficou com carinha triste",
    "Minha calopsita canta música do Legião Urbana, talentosa",
    "Dois gatos em casa é entretenimento 24 horas por dia",
    "Meu cachorro adora tomar banho de mangueira no quintal",
    "Tartaruga de estimação completou 15 anos, longevidade incrível",
    "Golden retriever é a raça mais carinhosa que existe",
]

# ═══════════════════════════════════════════════════════════════════════
# COMENTÁRIOS REALISTAS
# ═══════════════════════════════════════════════════════════════════════

COMENTARIOS = [
    "Muito bom! Concordo demais", "Que legal isso!", "Arrasou!",
    "Parabéns! Merece muito", "Ri demais com isso kkkkk",
    "Verdade, penso igual", "Quero ir também!", "Que lindo!",
    "Top demais!", "Hahaha muito bom", "Saudade disso!",
    "Compartilhei com meus amigos", "Incrível!", "Show de bola",
    "Queria estar aí", "Que foto linda!", "Amei esse post",
    "Pensando nisso o dia inteiro", "Super concordo!",
    "Isso é muito importante", "Precisamos falar mais sobre isso",
    "Genial!", "Te entendo demais", "Força! Vai dar tudo certo",
    "Passando pra deixar meu like", "Conteúdo de qualidade",
    "Que delícia, manda a receita!", "Me identifiquei total",
    "Boa sorte! Torcendo por você", "Que dia foi esse hein",
    "Maravilhoso!", "Orgulho de você!", "Meus parabéns!",
    "Conta mais!", "Fiquei curioso agora", "Ótima dica!",
    "Vou tentar fazer isso também", "Muito inspirador",
    "Que demais! Fiquei feliz por você", "Tô rindo até agora",
]


def populate():
    with app.app_context():
        # ── RESET COMPLETO ────────────────────────────────────────
        print("Resetando banco de dados...")
        db.drop_all()
        db.create_all()
        print("Banco recriado.\n")

        # ── CRIAR USUÁRIOS ────────────────────────────────────────
        print("Criando 100 usuários...")
        users = []
        senha_hash = bcrypt.generate_password_hash("Senha123!").decode("utf-8")

        for nome, username, idade in NOMES:
            email = f"{username.replace('.', '')}@conecta.com"
            user = User(
                nome=nome, username=username, email=email,
                senha=senha_hash, idade=idade,
                perfil_privado=random.random() < 0.1,
                tema=random.choice(["claro", "claro", "claro", "escuro"])
            )
            db.session.add(user)
            users.append(user)

        db.session.commit()
        print(f"  {len(users)} usuários criados.\n")

        # Separar por faixa etária
        adultos = [u for u in users if u.idade >= 18]
        adolescentes = [u for u in users if 14 <= u.idade < 18]
        criancas = [u for u in users if u.idade < 14]

        # ── CRIAR SEGUIDORES ─────────────────────────────────────
        print("Criando relações de seguidores...")
        follows_count = 0
        for user in users:
            n_seguir = random.randint(5, 25)
            possiveis = [u for u in users if u.id != user.id]
            para_seguir = random.sample(possiveis, min(n_seguir, len(possiveis)))
            for target in para_seguir:
                if not user.is_following(target):
                    user.followed.append(target)
                    follows_count += 1
        db.session.commit()
        print(f"  {follows_count} relações criadas.\n")

        # ── CRIAR PUBLICAÇÕES ─────────────────────────────────────
        print("Criando publicações (classificação via modelo de IA)...")

        todas_posts = []
        stats = {"adulto": 0, "neutro": 0, "infantil": 0}

        def criar_post(user, texto, minutos_atras):
            classificacao = classificar_local(texto)
            post = Post(
                texto=texto, classificacao_local=classificacao,
                user_id=user.id,
                data_publicacao=datetime.utcnow() - timedelta(minutes=minutos_atras),
                likes=0, comments_count=0
            )
            db.session.add(post)
            todas_posts.append(post)
            stats[classificacao] = stats.get(classificacao, 0) + 1

        minutos = 1

        # Adultos postam de tudo
        for texto in POSTS_COTIDIANO:
            criar_post(random.choice(adultos), texto, minutos)
            minutos += random.randint(5, 30)

        for texto in POSTS_TRABALHO:
            criar_post(random.choice(adultos), texto, minutos)
            minutos += random.randint(5, 30)

        for texto in POSTS_ESPORTE:
            criar_post(random.choice(adultos + adolescentes), texto, minutos)
            minutos += random.randint(5, 30)

        for texto in POSTS_TECH:
            criar_post(random.choice(adultos + adolescentes), texto, minutos)
            minutos += random.randint(5, 25)

        for texto in POSTS_OPINIAO:
            criar_post(random.choice(adultos), texto, minutos)
            minutos += random.randint(10, 40)

        for texto in POSTS_HUMOR:
            criar_post(random.choice(adultos + adolescentes), texto, minutos)
            minutos += random.randint(5, 20)

        for texto in POSTS_VIAGEM:
            criar_post(random.choice(adultos), texto, minutos)
            minutos += random.randint(10, 40)

        for texto in POSTS_RELACIONAMENTO:
            criar_post(random.choice(adultos), texto, minutos)
            minutos += random.randint(10, 30)

        for texto in POSTS_MUSICA:
            criar_post(random.choice(adultos + adolescentes), texto, minutos)
            minutos += random.randint(5, 25)

        # Estudantes e adolescentes
        for texto in POSTS_ESTUDANTE:
            criar_post(random.choice(adolescentes + criancas), texto, minutos)
            minutos += random.randint(5, 20)

        for texto in POSTS_ADOLESCENTE:
            criar_post(random.choice(adolescentes), texto, minutos)
            minutos += random.randint(5, 20)

        # Crianças
        for texto in POSTS_CRIANCA:
            criar_post(random.choice(criancas), texto, minutos)
            minutos += random.randint(5, 25)

        # Conteúdo adulto (só adultos postam)
        for texto in POSTS_ADULTO_REALISTA:
            criar_post(random.choice(adultos), texto, minutos)
            minutos += random.randint(5, 20)

        # Posts ambíguos (adultos e adolescentes mais velhos)
        for texto in POSTS_AMBIGUOS:
            criar_post(random.choice(adultos), texto, minutos)
            minutos += random.randint(5, 25)

        # Posts extras — cotidiano, saúde, comida, pets
        for texto in POSTS_EXTRA_1:
            criar_post(random.choice(adultos + adolescentes), texto, minutos)
            minutos += random.randint(5, 25)

        for texto in POSTS_EXTRA_2:
            criar_post(random.choice(adultos), texto, minutos)
            minutos += random.randint(5, 25)

        for texto in POSTS_EXTRA_3:
            criar_post(random.choice(adultos + adolescentes), texto, minutos)
            minutos += random.randint(5, 20)

        for texto in POSTS_EXTRA_4:
            criar_post(random.choice(users), texto, minutos)
            minutos += random.randint(5, 20)

        db.session.commit()
        print(f"  {len(todas_posts)} publicações criadas.")
        print(f"    Classificação automática: {stats}\n")

        # ── CURTIDAS ──────────────────────────────────────────────
        print("Gerando curtidas...")
        likes_count = 0
        for post in todas_posts:
            # Posts variados recebem entre 0 e 30 curtidas
            n_likes = random.randint(0, 30)
            possiveis = [u for u in users if u.id != post.user_id]
            quem_curtiu = random.sample(possiveis, min(n_likes, len(possiveis)))
            for user in quem_curtiu:
                like = PostLike(user_id=user.id, post_id=post.id)
                db.session.add(like)
                post.likes += 1
                likes_count += 1

        db.session.commit()
        print(f"  {likes_count} curtidas geradas.\n")

        # ── COMENTÁRIOS ───────────────────────────────────────────
        print("Gerando comentários...")
        comments_count = 0
        for post in todas_posts:
            n_comments = random.randint(0, 6)
            possiveis = [u for u in users if u.id != post.user_id]
            quem_comenta = random.sample(possiveis, min(n_comments, len(possiveis)))
            for user in quem_comenta:
                texto_com = random.choice(COMENTARIOS)
                comment = Comment(
                    texto=texto_com, user_id=user.id,
                    post_id=post.id,
                    data=post.data_publicacao + timedelta(minutes=random.randint(1, 120)),
                    likes=random.randint(0, 5)
                )
                db.session.add(comment)
                post.comments_count += 1
                comments_count += 1

        db.session.commit()
        print(f"  {comments_count} comentários gerados.\n")

        # ── CURTIDAS EM COMENTÁRIOS ───────────────────────────────
        print("Gerando curtidas em comentários...")
        all_comments = Comment.query.all()
        comment_likes_count = 0
        for comment in all_comments:
            n = random.randint(0, 4)
            possiveis = [u for u in users if u.id != comment.user_id]
            quem_curtiu = random.sample(possiveis, min(n, len(possiveis)))
            for user in quem_curtiu:
                cl = CommentLike(user_id=user.id, comment_id=comment.id)
                db.session.add(cl)
                comment.likes += 1
                comment_likes_count += 1

        db.session.commit()
        print(f"  {comment_likes_count} curtidas em comentários.\n")

        # ── NOTIFICAÇÕES SAMPLE ───────────────────────────────────
        print("Gerando notificações de exemplo...")
        notifs_count = 0
        for user in random.sample(users, 40):
            for _ in range(random.randint(1, 5)):
                outro = random.choice([u for u in users if u.id != user.id])
                tipos = [
                    ("like", f"❤️ {outro.nome} curtiu sua publicação."),
                    ("comment", f"💬 {outro.nome} comentou na sua publicação."),
                    ("follow", f"👤 @{outro.username} começou a seguir você!"),
                ]
                tipo, msg = random.choice(tipos)
                notif = Notification(
                    user_id=user.id, tipo=tipo, mensagem=msg,
                    data=datetime.utcnow() - timedelta(minutes=random.randint(1, 5000)),
                    lida=random.random() < 0.4
                )
                db.session.add(notif)
                notifs_count += 1

        db.session.commit()
        print(f"  {notifs_count} notificações geradas.\n")

        # ── BOOST TRENDING ────────────────────────────────────────
        print("Impulsionando posts para trending...")
        posts_recentes = Post.query.filter(
            Post.data_publicacao >= datetime.utcnow() - timedelta(hours=24)
        ).all()

        if posts_recentes:
            trending_picks = random.sample(posts_recentes, min(8, len(posts_recentes)))
            for post in trending_picks:
                boost_likes = random.randint(20, 50)
                possiveis = [u for u in users if u.id != post.user_id]
                for user in random.sample(possiveis, min(boost_likes, len(possiveis))):
                    existing = PostLike.query.filter_by(user_id=user.id, post_id=post.id).first()
                    if not existing:
                        db.session.add(PostLike(user_id=user.id, post_id=post.id))
                        post.likes += 1

                boost_comments = random.randint(5, 15)
                for user in random.sample(possiveis, min(boost_comments, len(possiveis))):
                    c = Comment(
                        texto=random.choice(COMENTARIOS),
                        user_id=user.id, post_id=post.id,
                        data=datetime.utcnow() - timedelta(minutes=random.randint(1, 300)),
                        likes=random.randint(0, 8)
                    )
                    db.session.add(c)
                    post.comments_count += 1

            db.session.commit()
            print(f"  {len(trending_picks)} posts impulsionados para trending.\n")

        # ── RESUMO FINAL ─────────────────────────────────────────
        total_posts = Post.query.count()
        total_likes = PostLike.query.count()
        total_comments = Comment.query.count()
        total_users = User.query.count()
        adulto_count = Post.query.filter_by(classificacao_local="adulto").count()
        neutro_count = Post.query.filter_by(classificacao_local="neutro").count()
        infantil_count = Post.query.filter_by(classificacao_local="infantil").count()

        print("=" * 60)
        print("POPULAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
        print(f"  Usuários:     {total_users}")
        print(f"  Publicações:  {total_posts}")
        print(f"    - adulto:   {adulto_count}")
        print(f"    - neutro:   {neutro_count}")
        print(f"    - infantil: {infantil_count}")
        print(f"  Curtidas:     {total_likes}")
        print(f"  Comentários:  {total_comments}")
        print(f"  Seguidores:   {follows_count}")
        print("=" * 60)
        print("\nContas de teste (senha: Senha123!):")
        print("  Adulto:       lucas.oli (24 anos)")
        print("  Adulto:       fe.costa (28 anos)")
        print("  Adolescente:  miguel.t (17 anos)")
        print("  Adolescente:  sofia.teen (16 anos)")
        print("  Criança:      pedrinho.k (12 anos)")
        print("  Criança:      mariazinha (10 anos)")


if __name__ == "__main__":
    populate()
