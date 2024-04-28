from typing import List
import string


ESPERANTO_CHARACTERS = string.ascii_letters + 'ĈĜĤĴŜŬĉĝĥĵŝŭ'


result_cache = {}

# tokenize_word
def esperanto_word_split(w, dictionary):
    if w in result_cache:
        return result_cache[w]
    if not w:
        return [[]]
    result = []
    for i in range(1, len(w) + 1):
        if w[:i].lower() in dictionary:
            postfix_result: List[List[str]] = list(esperanto_word_split(w[i:], dictionary=dictionary))
            #print('postfix_result', w, i, w[i], postfix_result)
            for j in range(len(postfix_result)):
                postfix_result[j] = [w[:i]] + postfix_result[j]
            result.extend(postfix_result)
    #print('Returning', f'tokenize_word({w})={result}')
    result_cache[w] = result
    return result

# 世界语文档分词器
def esperanto_tokenize(text):
    result: List[str] = []
    last_part = ''
    for pos in range(len(text) + 1):
        if (
            pos == len(text) or (
                len(last_part) > 0 and \
                (
                    (last_part[-1] in ESPERANTO_CHARACTERS and text[pos] not in ESPERANTO_CHARACTERS) or
                    (last_part[-1] not in ESPERANTO_CHARACTERS and text[pos] in ESPERANTO_CHARACTERS)
                )
            )
        ):
            result.append(last_part)
            last_part = ''
        if pos != len(text):
            last_part += text[pos]
    return result

def esperanto_tokenize_and_analyze_file(input_file: str, output_file: str, dictionary):

    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as file:
        text = file.read()

    document = esperanto_tokenize(text)

    with open(output_file, 'w', encoding='utf-8') as file:
        for i in range(len(document)):
            if document[i][0] not in ESPERANTO_CHARACTERS:
                file.write(document[i])
                continue
            possible_splits = esperanto_word_split(document[i], dictionary=dictionary)
            if possible_splits:
                annotation = ','.join(['|'.join(_) for _ in possible_splits])
            else:
                annotation = 'kontroloto'
            file.write(document[i] + f'[[{annotation}]]')

if __name__ == '__main__':
    MORPHEME_FILES = [
        './vortaro/prefikso.txt',
        './vortaro/radiko.txt',
        './vortaro/sufikso.txt',
        './vortaro/tabelvorto.txt',
        './vortaro/vorteto.txt',
    ]

    dictionary_list = []

    for file in MORPHEME_FILES:
        data = open(file, encoding='utf-8').read()
        if data.startswith('{'):
            dictionary_list.extend([w.strip() for w in data[1:-1].split(',')])
        else:
            dictionary_list.extend([w.strip() for w in data.strip().split('\n')])

    esperanto_tokenize_and_analyze_file('input.txt', 'output.txt', dictionary=set(dictionary_list + ['a', 'e', 'i', 'o', 'u']))
    #print(tokenize_word('abcab'))

# Maljunulo| — |Ho|, |kompreneble|. |Bonvolu| |sidiĝi|. ( |Al| |la| |knabino|. ) Alportu akvon, infano, purigu la glason antaŭe.