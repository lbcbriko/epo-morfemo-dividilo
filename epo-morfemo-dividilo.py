import sys
import regex as re
import string

if len(sys.argv) != 3:
    print("Usage: python3 morfemdividilo.py INPUTFILE OUTPUTFILE")
    sys.exit(1)
    
inputname = sys.argv[1]
outputname = sys.argv[2]

def akuzativo(input_file, output_file):
    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as file:
        text = file.read()

    # 定义正则表达式来匹配特定的'n'，排除'en','jen'以及'n'后紧跟'-'的情况
    pattern = r'(?<!\b(e|j)e)n(?!\-)(?=\s|[!-\/:-@\[-`{-~])'

    # 定义回调函数以根据匹配的'n'是大写还是小写来决定插入的分隔符后的'n'
    def replace_func(match):
        matched_n = match.group(0)
        # 判断匹配到的'n'是否为大写
        if matched_n.isupper():
            return '_N'
        else:
            return '_n'
    
    # 执行替换
    modified_text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)

    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(modified_text)

    print("Step 1 completed: Separator inserted before 'n', preserving case and ignoring 'n-' cases.")

# 调用
akuzativo(inputname, 'cache1')


def pluralo(input_file, output_file):
    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as file:
        text = file.read()

    # 定义正则表达式来匹配特定的'j'，忽略单独出现的'j'和位于连词符"-"后的'j'
    # 匹配其后为空格、换行符、标点符号和"_n"的'j'
    pattern = r'(?<=\p{L})j(?=(\s|[\p{P}]|_n|$))'

    # 定义回调函数以根据匹配的'j'是大写还是小写来决定插入的分隔符后的'j'
    def replace_func(match):
        matched_j = match.group(0)
        # 判断匹配到的'j'是否为大写
        if matched_j.isupper():
            return '_J'
        else:
            return '_j'
    
    # 执行替换
    modified_text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)

    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(modified_text)

    print("Step 2 completed: Separator inserted before 'j', preserving case and applying specified exclusions.")

# 调用
pluralo('cache1', 'cache2')

def finitivo(input_file, output_file):
    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as file:
        text = file.read()

    # 定义正则表达式来匹配指定的后缀前的位置
    pattern = r'(?<=\p{L})(as|is|os|us|u)(?=(\s|[\p{P}]|$))'

    # 定义回调函数以根据匹配的后缀是大写还是小写来决定插入的分隔符
    def replace_func(match):
        matched_suffix = match.group(0)
        # 判断匹配到的后缀是否全部为大写（考虑单个字符'U'的情况）
        if matched_suffix.isupper() or matched_suffix == 'U':
            return f'_{matched_suffix.upper()}'
        else:
            return f'_{matched_suffix.lower()}'
    
    # 执行替换
    modified_text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)

    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(modified_text)

    print("Step 3 completed: Separator inserted before specified suffixes, preserving case.")

# 调用
finitivo('cache2', 'cache3')


def vortspeco(input_file, output_file):
    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as file:
        text = file.read()

    # 定义正则表达式来匹配指定的单个字母（"a", "o", "e", "i"）前的位置
    # 考虑其后可能紧跟空格、换行符、标点符号或特定的后缀（"_j", "_n", "_o"）
    pattern = r'(?<=\p{L})(a|o|e|i)(?=(\s|[\p{P}]|_j|_n|(_o)?$))'

    # 定义回调函数以根据匹配的字母是大写还是小写来决定插入的分隔符
    def replace_func(match):
        matched_letter = match.group(0)
        # 判断匹配到的字母是否为大写
        if matched_letter.isupper():
            return f'_{matched_letter.upper()}'
        else:
            return f'_{matched_letter.lower()}'
    
    # 执行替换
    modified_text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)

    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(modified_text)

    print("Steps 4-6 completed: Separator inserted before specified vowels, preserving case.")

# 调用
vortspeco('cache3', 'cache6')


def genro(input_file, output_file):
    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as file:
        text = file.read()

    # 定义正则表达式来匹配"in"后紧接"_o"的情况
    pattern = r'in(?=(_o|_e|_a))'

    # 定义回调函数以根据匹配的"in"是大写还是小写来决定插入的分隔符
    def replace_func(match):
        matched_in = match.group(0)
        # 判断匹配到的"in"是否为大写
        if matched_in == 'IN':
            return f'_IN'
        else:
            return f'_in'
    
    # 执行替换
    modified_text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)

    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(modified_text)

    print("Step 7 completed: Separator inserted before 'in' followed by '_o', preserving case for specific cases like In_o, IN_O, in_o.")

genro('cache6', 'cache7')


def participo(input_file, output_file):
    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as file:
        text = file.read()

    # 定义正则表达式，匹配指定的后缀，并考虑其后可能紧跟的特定字符串
    # 使用负向前视断言确保不处理以"Esperant"开头的词
    pattern = r'(?<!Esperant)(ant|ont|int|at|ot|it)(?=(_a|_e|_o|$))'

    # 定义回调函数以根据匹配的后缀是大写还是小写来决定插入的分隔符
    def replace_func(match):
        matched_suffix = match.group(0)
        # 判断匹配到的后缀是否全部为大写
        if matched_suffix.isupper():
            return f'_{matched_suffix}'
        else:
            return f'_{matched_suffix.lower()}'
    
    # 执行替换
    modified_text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)

    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(modified_text)

    print("Step 8 completed: Separator inserted before specified suffixes, preserving case and excluding 'Esperant_'.")

participo('cache7', 'cache8')


def aliaj_sufiksoj_prilabori(input_text, suffixes):
    # 构建正则表达式以匹配所有指定的后缀，这些后缀后面紧跟分隔符"_"
    suffix_pattern = '|'.join(map(re.escape, suffixes))
    # 使用regex库改进匹配模式
    re_pattern = re.compile(r'(\b\w*?)(' + suffix_pattern + r')(?=_)', re.IGNORECASE)

    def replace_func(match):
        # 将匹配到的后缀前插入分隔符"_"
        return match.group(1) + '_' + match.group(2)

    # 应用正则表达式并在符合条件的后缀前插入分隔符"_"
    modified_text = re_pattern.sub(replace_func, input_text)

    return modified_text

def aliaj_sufiksoj_cxefa(input_file, output_file):
    # 定义需要插入分隔符的后缀集合
    suffixes = {
        'aĉ', 'ad', 'aĵ', 'an', 'ar', 'ĉj', 'ebl', 'ec', 'eg', 'ej', 'em', 'end', 'er', 'estr', 'et',
        'id', 'ig', 'iĝ', 'il', 'ind', 'ing', 'ism', 'ist', 'nj', 'obl', 'on', 'op', 'uj', 'ul', 'um'
    }

    # 读取输入文件内容
    with open(input_file, 'r', encoding='utf-8') as file:
        input_text = file.read()

    # 处理文本
    modified_text = aliaj_sufiksoj_prilabori(input_text, suffixes)

    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(modified_text)

    print("Processing completed. The output file has been updated.")

aliaj_sufiksoj_cxefa('cache8', 'cache9')



def kontroli_prigotajxon(input_text):
    # 删除位于文档开头和末尾的分隔符
    text = re.sub(r'^_+|_+$', '', input_text)
    # 删除一侧为空格、标点符号或换行符的分隔符
    text = re.sub(r'(?<=\s)_+|_+(?=\s)|(?<=[^\w\s])_+|_+(?=[^\w\s])', '', text)
    # 将连续的分隔符替换为仅一个分隔符
    text = re.sub(r'_+', '_', text)
    return text

def purigi_dividilon(input_file, output_file):
    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as file:
        input_text = file.read()

    # 清理分隔符
    cleaned_text = kontroli_prigotajxon(input_text)

    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(cleaned_text)

    print("Step 10 completed: Unnecessary separators removed, and consecutive separators consolidated.")
    
purigi_dividilon('cache9', 'cache10')



def insert_separators_for_consecutive_prefixes(input_text, prefixes):
    sorted_prefixes = sorted(prefixes, key=len, reverse=True)
    i = 0
    while i < len(input_text):
        for prefix in sorted_prefixes:
            prefix_len = len(prefix)
            if input_text[i:].lower().startswith(prefix.lower()) and (i + prefix_len == len(input_text) or input_text[i + prefix_len] not in ['_'] + list(prefixes)):
                input_text = input_text[:i + prefix_len] + "_" + input_text[i + prefix_len:]
                i += prefix_len
                break
        else:
            i += 1
    return input_text

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


# 调用处理函数
process_prefixes('cache10', 'cache11')
