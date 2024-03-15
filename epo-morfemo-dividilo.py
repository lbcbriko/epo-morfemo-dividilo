import sys
import regex as re
import string

if len(sys.argv) != 3:
    print("Usage: python3 morfemdividilo.py INPUTFILE OUTPUTFILE")
    sys.exit(1)
    
inputname = sys.argv[1]
outputname = sys.argv[2]

def akuzativo(input_file, output_file):
    # Legi enigitan dosieron
    with open(input_file, 'r', encoding='utf-8') as file:
        text = file.read()

    # Difini regulan esprimon来匹配特定的'n'，排除'en','jen'以及'n'后紧跟'-'的情况
    pattern = r'(?<!\b(e|j)e)n(?!\-)(?=\s|[!-\/:-@\[-`{-~])'

    # Difini 回调函数以根据匹配的'n'是大写还是小写来决定插入的分隔符后的'n'
    def replace_func(match):
        matched_n = match.group(0)
        # Kontroli usklon
        if matched_n.isupper():
            return '_N'
        else:
            return '_n'
    
    # Anstataŭi
    modified_text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)

    # Skribi eksterigotan dosieron
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(modified_text)

    print("Step 1 completed: Separator inserted before 'n', preserving case and ignoring 'n-' cases.")

# Voki funkcion
akuzativo(inputname, 'cache1')


def pluralo(input_file, output_file):
    # Legi enigitan dosieron
    with open(input_file, 'r', encoding='utf-8') as file:
        text = file.read()

    # Difini regulan esprimon 来匹配特定的'j'，忽略单独出现的'j'和位于连词符"-"后的'j'
    # 匹配其后为空格、换行符、标点符号和"_n"的'j'
    pattern = r'(?<=\p{L})j(?=(\s|[\p{P}]|_n|$))'

    # Difini 回调函数以根据匹配的'j'是大写还是小写来决定插入的分隔符后的'j'
    def replace_func(match):
        matched_j = match.group(0)
        # Kontroli usklon
        if matched_j.isupper():
            return '_J'
        else:
            return '_j'
    
    # Anstataŭi
    modified_text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)

    # Skribi eksterigotan dosieron
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(modified_text)

    print("Step 2 completed: Separator inserted before 'j', preserving case and applying specified exclusions.")

# Voki funkcion
pluralo('cache1', 'cache2')

def finitivo(input_file, output_file):
    # Legi enigitan dosieron
    with open(input_file, 'r', encoding='utf-8') as file:
        text = file.read()

    # Difini regulan esprimon 来匹配指定的后缀前的位置
    pattern = r'(?<=\p{L})(as|is|os|us|u)(?=(\s|[\p{P}]|$))'

    # Difini 回调函数以根据匹配的后缀是大写还是小写来决定插入的分隔符
    def replace_func(match):
        matched_suffix = match.group(0)
        # 判断匹配到的后缀是否全部为大写（考虑单个字符'U'的情况）
        if matched_suffix.isupper() or matched_suffix == 'U':
            return f'_{matched_suffix.upper()}'
        else:
            return f'_{matched_suffix.lower()}'
    
    # Anstataŭi
    modified_text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)

    # Skribi eksterigotan dosieron
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(modified_text)

    print("Step 3 completed: Separator inserted before specified suffixes, preserving case.")

# Voki funkcion
finitivo('cache2', 'cache3')


def vortspeco(input_file, output_file):
    # Legi enigitan dosieron
    with open(input_file, 'r', encoding='utf-8') as file:
        text = file.read()

    # Difini regulan esprimon 来匹配指定的单个字母（"a", "o", "e", "i"）前的位置
    # 考虑其后可能紧跟空格、换行符、标点符号或特定的后缀（"_j", "_n", "_o"）
    pattern = r'(?<=\p{L})(a|o|e|i)(?=(\s|[\p{P}]|_j|_n|(_o)?$))'

    # Difini 回调函数以根据匹配的字母是大写还是小写来决定插入的分隔符
    def replace_func(match):
        matched_letter = match.group(0)
        # Kontroli usklon
        if matched_letter.isupper():
            return f'_{matched_letter.upper()}'
        else:
            return f'_{matched_letter.lower()}'
    
    # Anstataŭi
    modified_text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)

    # Skribi eksterigotan dosieron
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(modified_text)

    print("Steps 4-6 completed: Separator inserted before specified vowels, preserving case.")

# Voki funkcion
vortspeco('cache3', 'cache6')

"""
Tiu ĉi parto estas funkcio por prilabori sufikson "-in-" k participoj individue. 
Tamen la vicordo ne ĉiam estas ĉe la fino, ekz. "Ŝi estas filineto  de Maria". 
Pro tio, ĉiuj sufiksoj estas kunmetitaj en nur 1 funkcio nun.

def genro(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        text = file.read()

    pattern = r'in(?=(_o|_e|_a))'

    def replace_func(match):
        matched_in = match.group(0)
        if matched_in == 'IN':
            return f'_IN'
        else:
            return f'_in'
    
    modified_text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(modified_text)

    print("Step 7 completed: Separator inserted before 'in' followed by '_o', preserving case for specific cases like In_o, IN_O, in_o.")

genro('cache6', 'cache7')


def participo(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        text = file.read()

    pattern = r'(?<!Esperant)(ant|ont|int|at|ot|it)(?=(_a|_e|_o|$))'

    def replace_func(match):
        matched_suffix = match.group(0)
        if matched_suffix.isupper():
            return f'_{matched_suffix}'
        else:
            return f'_{matched_suffix.lower()}'
    
    modified_text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(modified_text)

    print("Step 8 completed: Separator inserted before specified suffixes, preserving case and excluding 'Esperant_'.")

participo('cache7', 'cache8')

"""

def aliaj_sufiksoj_prilabori(input_text, suffixes):
    # 构建regulan esprimon 以匹配所有指定的后缀，这些后缀后面紧跟分隔符"_"
    suffix_pattern = '|'.join(map(re.escape, suffixes))
    # 使用regex库改进匹配模式
    re_pattern = re.compile(r'(\b\w*?)(' + suffix_pattern + r')(?=_)', re.IGNORECASE)

    def replace_func(match):
        # 将匹配到的后缀前插入分隔符"_"
        return match.group(1) + '_' + match.group(2)

    # 应用regulan esprimon 并在符合条件的后缀前插入分隔符"_"
    modified_text = re_pattern.sub(replace_func, input_text)

    return modified_text

def aliaj_sufiksoj_cxefa(input_file, output_file):
    # Defini sufiksaron
    suffixes = {
        'aĉ', 'ad', 'aĵ', 'an', 'ar', 'ĉj', 'ebl', 'ec', 'eg', 'ej', 'em', 'end', 'er', 'estr', 'et',
        'id', 'ig', 'iĝ', 'il', 'in', 'ind', 'ing', 'ism', 'ist', 'nj', 'obl', 'on', 'op', 'uj', 'ul', 
        'um', 'ant', 'at', 'ont', 'ot', 'int', 'it'
    }

    with open(input_file, 'r', encoding='utf-8') as file:
        input_text = file.read()

    modified_text = aliaj_sufiksoj_prilabori(input_text, suffixes)

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(modified_text)

    print("Processing completed. The output file has been updated.")

aliaj_sufiksoj_cxefa('cache6', 'cache9')



def kontroli_prigotajxon(input_text):
    # Forigi dividilojn ĉe komenco aŭ fino de dosiero
    text = re.sub(r'^_+|_+$', '', input_text)
    # Forigi dividilon kun spaco, interpunkcio aŭ novalinio ĉe iu ajn flanko
    text = re.sub(r'(?<=\s)_+|_+(?=\s)|(?<=[^\w\s])_+|_+(?=[^\w\s])', '', text)
    # Anstataŭi plurajn dividilojn per nur unu
    text = re.sub(r'_+', '_', text)
    return text

def purigi_dividilon(input_file, output_file):
    # Legi enigitan dosieron
    with open(input_file, 'r', encoding='utf-8') as file:
        input_text = file.read()

    # prigi misdividilojn
    cleaned_text = kontroli_prigotajxon(input_text)

    # Skribi eksterigotan dosieron
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(cleaned_text)

    print("Step 10 completed: Unnecessary separators removed, and consecutive separators consolidated.")
    
purigi_dividilon('cache9', 'cache10')


def insert_separators_for_consecutive_prefixes(input_text, prefixes):
    # 将前缀按长度降序排序并转义，以确保长前缀优先匹配
    prefix_pattern = '|'.join(sorted(map(re.escape, prefixes), key=len, reverse=True))
    # 构建匹配前缀的regulan esprimon ，忽略大小写
    regex_pattern = re.compile(r'(?<=^|[\s_])(' + prefix_pattern + r')(?=\w)', re.IGNORECASE)

    # 将输入文本转换为列表，每个字符为一个元素
    chars = list(input_text)
    # 遍历字符列表并寻找匹配的前缀
    i = 0
    while i < len(chars):
        match = regex_pattern.match(''.join(chars[i:]))
        if match:
            end = i + match.end()
            chars.insert(end, '_')  # 在匹配的前缀后插入分隔符
            i = end  # 更新索引以跳过刚刚插入的分隔符
        i += 1  # 移动到下一个字符
    return ''.join(chars)  # 将字符列表合并回字符串

def process_prefixes(input_file, output_file):
    prefixes = {
        'bo', 'ĉef', 'dis', 'ek', 'eks', 'ge', 'mal', 'mis', 'pra', 're', 'afro', 'anti', 'arĥi', 'aŭdio',
        'aŭto', 'bio', 'des', 'eko', 'eŭro', 'hiper', 'infra', 'ko', 'kver', 'makro', 'meta', 'mikro',
        'mini', 'mono', 'pre', 'proto', 'pseŭdo', 'retro', 'san', 'semi', 'stif', 'tele', 'termo', 'ultra',
        'video'
    }

    with open(input_file, 'r', encoding='utf-8') as file:
        input_text = file.read()

    modified_text = insert_separators_for_consecutive_prefixes(input_text, prefixes)

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(modified_text)

    print(f"Processing completed. The output file {output_file} has been updated.")


# Voki funkcion
process_prefixes('cache10', 'cache11')
