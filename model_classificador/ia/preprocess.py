import re
import unicodedata


def clean_text(texto):
    """
    Pipeline de normalização robusto contra ofuscação de conteúdo adulto.
    
    Técnicas cobertas:
    1. Lowercase + remoção de acentos
    2. Leetspeak (ex: s3x0 → sexo)  
    3. Pontuação/separadores no meio de palavras (ex: s.e.x.o → sexo)
    4. Caracteres repetidos (ex: seeeeexo → sexo)
    5. Espaços intencionais (ex: "s e x o" → "sexo")
    6. Caracteres unicode especiais (ex: ⓢⓔⓧⓞ)
    7. Emojis removidos para evitar ruído
    """
    if not isinstance(texto, str):
        return ""

    # 1. Lowercase
    texto = texto.lower()

    # 2. Normalizar unicode homoglyphs (caracteres visuais idênticos)
    # Cirílico, grego, fullwidth, etc. → ASCII
    homoglyph_map = {
        'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'у': 'y',
        'х': 'x', 'і': 'i', 'ⓢ': 's', 'ⓔ': 'e', 'ⓧ': 'x', 'ⓞ': 'o',
        'ⓟ': 'p', 'ⓤ': 'u', 'ⓣ': 't', 'ⓐ': 'a', 'ⓝ': 'n', 'ⓓ': 'd',
        'ⓡ': 'r', 'ⓘ': 'i', 'ⓛ': 'l', 'ⓜ': 'm', 'ⓒ': 'c', 'ⓑ': 'b',
        'ⓕ': 'f', 'ⓖ': 'g', 'ⓗ': 'h', 'ⓙ': 'j', 'ⓚ': 'k',
        'ⓩ': 'z', 'ⓥ': 'v', 'ⓦ': 'w', 'ⓨ': 'y',
        '𝐚': 'a', '𝐛': 'b', '𝐜': 'c', '𝐝': 'd', '𝐞': 'e',
        'ꜱ': 's', 'ᴇ': 'e', 'ᴏ': 'o', 'ᴀ': 'a', 'ᴜ': 'u',
    }
    for char, rep in homoglyph_map.items():
        texto = texto.replace(char, rep)

    # 3. Remover acentos (avião → aviao, cocaína → cocaina)
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

    # 4. Leetspeak avançado
    leetspeak_map = {
        '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's',
        '@': 'a', '$': 's', '7': 't', '8': 'b', '!': 'i',
        '|': 'l', '(': 'c', '+': 't', '¥': 'y', '€': 'e',
        '£': 'l', '¢': 'c', '²': 's', '³': 'e',
    }
    for char, rep in leetspeak_map.items():
        texto = texto.replace(char, rep)

    # 5. Remover emojis e caracteres especiais unicode mantendo letras e espaços
    texto = re.sub(
        r'[^\w\s]',  # remove tudo que não seja alfanumérico ou espaço
        ' ',
        texto,
        flags=re.UNICODE
    )

    # 6. Remover separadores no meio de palavras (s.e.x.o, s-e-x-o, s_e_x_o)
    # Já tratado pelo passo anterior, mas garantir
    texto = re.sub(r'(?<=\w)[._\-\*\#\+](?=\w)', '', texto)

    # 7. Colapsar caracteres repetidos (seeeeexo → seexo → sexo)
    texto = re.sub(r'(.)\1{2,}', r'\1\1', texto)  # Max 2 repeats

    # 8. Detectar e juntar letras espaçadas intencionalmente
    # "s e x o" → "sexo", "p u t a" → "puta"
    # Verifica se o texto tem padrão de letras isoladas com espaço
    words = texto.split()
    rebuilt = []
    buffer = []
    for w in words:
        if len(w) == 1 and w.isalpha():
            buffer.append(w)
        else:
            if len(buffer) >= 3:
                # 3+ letras isoladas em sequência → juntar
                rebuilt.append(''.join(buffer))
            elif buffer:
                # Poucas letras isoladas, manter separadas
                rebuilt.extend(buffer)
            buffer = []
            rebuilt.append(w)
    if len(buffer) >= 3:
        rebuilt.append(''.join(buffer))
    elif buffer:
        rebuilt.extend(buffer)
    texto = ' '.join(rebuilt)

    # 9. Normalizar espaços múltiplos
    texto = re.sub(r'\s+', ' ', texto)

    return texto.strip()
