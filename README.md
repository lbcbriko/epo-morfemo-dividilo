# epo-morfemo-dividilo

Skripto por prilabori tekstojn en Esperanto, por dividi morfemojn en vortoj.

Script for processing Esperanto texts, to divide morphemes in words.

&nbsp;

Mi sincere petas samideanoj kunklopodi por NLP-iloj en Esperanto.

Pardonon, la dokumento kaj notoj ne pretiĝis. Mi tuj faros tion.

&nbsp;

# Paŝoj

Mi planis dividi morfemojn per jenaj paŝoj. Tiuj paŝoj fariĝos unu post la alia laŭ vico. Se iu proponas pli bonan logikon, ĝi povas ŝanĝiĝi.

## Nomvorto (✓programita)

1\. Por litero "n" antaŭ spaco, linioŝanĝilo aŭ interpunkcio, tajpi dividilon "\_" antaŭ ĝin;  

2\. Por litero "j" antaŭ spaco, linioŝanĝilo, interpunkcio aŭ "\_n", tajpi dividilon "\_" antaŭ ĝin;

## Finitivo (✓programita)

3\. Por morfemo "as", "is", "os", "us", "u", kiuj estas antaŭ spaco, linioŝanĝilo aŭ interpunkcio, tajpi dividilon "\_" antaŭ ĝin;

## Vortospeco & infinitivo (✓programita)

4\. Por morfemo "a", "o", kiuj estas antaŭ spaco, linioŝanĝilo, interpunkcio, "\_j" aŭ "\_n", tajpi dividilon "\_" antaŭ ĝin;

5\. Por morfemo "e", kiuj estas antaŭ spaco, linioŝanĝilo, interpunkcio aŭ "\_n", tajpi dividilon "\_" antaŭ ĝin, sed krom "ie";

6\. Por morfemo "i", kiuj estas antaŭ spaco, linioŝanĝilo, interpunkcio aŭ "\_o", tajpi dividilon "\_" antaŭ ĝin

## Genro (✓programita)

7\. Por "in" antaŭ "\_o", tajpi dividilon "\_" antaŭ ĝin; ekz. de "instruistino" al "instruist_in_o", de "FILIN_O" al "FIL_IN_O";

## Participo (✓programita)

Por morfemoj"ant", "ont", "int", "at", "ot", "it", kiuj antaŭ "\_a", "\_e", "\_o", entajpi dividilon antaŭ ilin, sed krom "Esperant_" ĉar ĉi tiu vorto kun nomuskla skribo estas propra nomo.
Ekz. Esperant_o aŭ Esperant_a estu ignorota, lernant_o prilaboriĝos al "lern_ant_o"，RINIT_O_J al RIN_IT_O_J.

## Aliaj sufiksoj (✓programita)

~~9\. 从后向前判断每个单词是否有位于词尾，其后紧跟分隔符"\_"且属于集合{aĉ,ad,aĵ,an,ar,ĉj,ebl,ec,eg,ej,em,end,er,estr,et,id,ig,iĝ,il,ind,ing,ism,ist,nj,obl,on,op,uj,ul,um}的元素，如果有则在其之前添加分隔符，并继续向前重复上述判断，直到不存在属于集合的元素。前文所述的紧跟在字符串后的分隔符应为一个单词中第一个，或逆序最后一个分隔符。~~  
~~例如对于malsanulejan_in_o，应从位于malsanulejan_in这部分的字符串开始判断，输出结果应为malsan_ul_ej_an_in_o~~

~~10\. 删除一侧为空格、标点符号或换行符的分隔符，删除位于文档开头和末尾的分隔符，将连续的分隔符替换为仅一个分隔符~~

## Prefiksoj (✓programita, sed bezonas rapidigi)

~~11\. 从前往后判断每个单词是否有位于开始，之前不存在任何字母的元素属于集合{bo,ĉef,dis,ek,eks,ge,mal,mis,pra,re,afro,anti,arĥi,aŭdio,aŭto,bio,des,eko,eŭro,hiper,infra,ko,kver,makro,meta,mikro,mini,mono,pre,proto,pseŭdo,retro,san,semi,stif,tele,termo,ultra,video}。如果有则在其之后添加分隔符"\_"，并继续向前重复上述判断，直到不存在属于集合的元素。~~  
~~例如对于geboav_o_j，输出结果应为ge_bo_av_o_j；对于Maldis_ig_i，输出结果应为Mal_dis_ig_i。该步骤逻辑与此前匹配集合中指定后缀的逻辑相似，但方向相反，且可能涉及到单词首字母大写、全部小写和全部大写情况，要求对它们均忽视大小写进行识别，但插入分隔符后的单词大小写应保持不变~~

## Radikoj (farota)

~~12\. 读取工作目录下的字典文件"radiko.txt"，对此前9、10两步插入的最后一个分隔符中间的部分，识别是否是以任意数量、任意顺序组合的radiko.txt中的字符串，并在其间插入分隔符；如果一个单词并未进行9、10步处理，依然检查它是否是radiko.txt中字符串的组合，并对其任意两个属于radiko.txt的字符串之间插入分隔符；对第11步，必须在两部分字符串均属于radiko.txt时才插入分隔符，否则不做处理；~~  
~~（该字典较大，且被处理的文本规模也较大。如果有可能进行优化或需要调用新的第三方库，请向我提出建议。）~~  
~~即判断是否有任意数量任意顺序的仅属于radiko.txt的字符串组合为新的字符串且仅位于空格、分隔符或连词符之间；被组合的元素之间不应有任何字母或符号；处理时将连词符视为字母；~~

## Malprilabori vortetojn (farota)

13\. Prilabori listo de vortetoj per antaŭaj paŝoj, kaj anstataŭi la prilaboritaj per originaj

## Dividi tabelvortojn (farota)

14\. anstataŭ {ĉia, ia, kia, nenia, tia, ĉial, ial, kial, nenial, tial, ĉiam, iam, kiam, neniam, tiam, ĉie, ie, kie, nenie, tie, ĉiel, iel, kiel, neniel, tiel, ĉies, ies, kies, nenies, ties, ĉio, io, kio, nenio, tio, ĉiom, iom, kiom, neniom, tiom, ĉiu, iu, kiu, neniu, tiu} per {ĉi_a, i_a, ki_a, neni_a, ti_a, ĉi_al, i_al, ki_al, neni_al, ti_al, ĉi_am, i_am, ki_am, neni_am, ti_am, ĉi_e, i_e, ki_e, neni_e, ti_e, ĉi_el, i_el, ki_el, neni_el, ti_el, ĉi_es, i_es, ki_es, neni_es, ti_es, ĉi_o, i_o, ki_o, neni_o, ti_o, ĉi_om, i_om, ki_om, neni_om, ti_om, ĉi_u, i_u, ki_u, neni_u, ti_u} 

Uskleco ne influas la serĉo, sed ne ŝanĝiĝos post antaŭigado

## Malprilabori misdividitajn morfemojn,  
ekz. "l_um_o", "hor_loĝ_o", "eks_kurs_o" (farota)

## Alia aldona pensado (farota, aŭ nur diskutota)

Mi pensis pri tio, ke la mala prilaboro poas okazi ne nur en la fina paŝo, sed multfoje sekvas aliajn misageblajn paŝojn, kaj la funkcio povas uziĝi plurfoje.

Ni povas prilabori liston de morfemoj (la dosiero "vortaro" kaj aldonaj estonte), tiel ni havos anstataŭ-interresponda listo, por eble pli rapida komputo. Ni povas plani speciala funkcio por krei la interreaponda listo per vortaro, do tio povas pli facile generiĝi.

Ni eble (mi ne certas) povas ordigi radikojn per longeco, tiel post kontroli mallongajn radikojn (ekz. "hor" k "loĝ"), ĝi ankoraŭ povas daŭre kontroli la longajn (ekz. "horloĝ")

Ni povas unue nur prilabori tiujn longajn morfemojn, kaj por tro mallongaj (ekz. "-i-"), kontroli poste per pli bonaj rimedoj aŭ manlaboro. 

Ni povas uzi eksterajn vortarojn kiel dosierojn anstataŭ rekte enkodigi la aron en programon, tiel oni povas pli facile novigi la vortaron laŭ bezono.

La programo eble povas fariĝi biblioteko, por pli komplikaj logikoj, aŭ nur uzi parton de la programo. (ekz nur kontroli sekson en iu teksto)

Originigilo povas ankaŭ kreiĝi per ĉi projekto, eble tio ne valoras por establi novan tenejon.
