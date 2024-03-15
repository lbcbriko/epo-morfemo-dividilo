# epo-morfemo-dividilo

(ATENTU: NE UZEBLA NUN!)

Skripto por prilabori tekstojn en Esperanto, por dividi morfemojn en vortoj.

Script for processing Esperanto texts, to divide morphemes in words.

&nbsp;

Pardonon, la dokumento kaj notoj ne pretiĝis. Mi tuj faros tion.

&nbsp;

## Kial mi faras tion?

Kvankam jam ekzistas programoj pri Esperanto, mi ankoraŭ volas ion pli facile kaj aŭtomate uzeblan. La celo de tiu ĉi programo finfine estos tia ilo, kiu povas krei korpuson de skanitaj bildoj. Jam ekzistas sufiĉe aŭtomata programo por rekoni optikajn signojn kaj kontroli literumadon, kaj aliaj datumpurigiloj. Post finprogrami morfemodividilon, pli da funkcio por konstrui korpuson aŭtomate estos farota.

&nbsp;

# Paŝoj

Mi planis dividi morfemojn per jenaj paŝoj. Tiuj paŝoj fariĝos unu post la alia laŭ vico. Se iu proponas pli bonan logikon, ĝi povas ŝanĝiĝi.

## Nomvorto (✓programita)

1\. Por litero "n" antaŭ spaco, novlinio aŭ interpunkcio, tajpi dividilon "\_" antaŭ ĝin;  

2\. Por litero "j" antaŭ spaco, novlinio, interpunkcio aŭ "\_n", tajpi dividilon "\_" antaŭ ĝin;

## Finitivo (✓programita)

3\. Por morfemo "as", "is", "os", "us", "u", kiuj estas antaŭ spaco, novlinio aŭ interpunkcio, tajpi dividilon "\_" antaŭ ĝin;

## Vortospeco & infinitivo (✓programita)

4\. Por morfemo "a", "o", kiuj estas antaŭ spaco, novlinio, interpunkcio, "\_j" aŭ "\_n", tajpi dividilon "\_" antaŭ ĝin;

5\. Por morfemo "e", kiuj estas antaŭ spaco, novlinio, interpunkcio aŭ "\_n", tajpi dividilon "\_" antaŭ ĝin, sed krom "ie";

6\. Por morfemo "i", kiuj estas antaŭ spaco, novlinio, interpunkcio aŭ "\_o", tajpi dividilon "\_" antaŭ ĝin

## Genro (✓programita)

7\. Por "in" antaŭ "\_o", tajpi dividilon "\_" antaŭ ĝin; ekz. de "instruistino" al "instruist_in_o", de "FILIN_O" al "FIL_IN_O";

## Participo (✓programita)

8\. Por morfemoj"ant", "ont", "int", "at", "ot", "it", kiuj antaŭ "\_a", "\_e", "\_o", entajpi dividilon antaŭ ilin, sed krom "Esperant_" ĉar ĉi tiu vorto kun nomuskla skribo estas propra nomo.

Ekz. Esperant_o aŭ Esperant_a estu ignorota, lernant_o prilaboriĝos al "lern_ant_o"，RINIT_O_J al RIN_IT_O_J.

## Aliaj sufiksoj (✓programita)

9\. De fino antaŭen serĉi elementojn, kiuj antaŭ la dividilo "\_" kaj en la aro {aĉ,ad,aĵ,an,ar,ĉj,ebl,ec,eg,ej,em,end,er,estr,et,id,ig,iĝ,il,ind,ing,ism,ist,nj,obl,on,op,uj,ul,um}, aldoni dividilon antaŭ ĝi, kaj daŭre refari tion, ĝis ne ekzistus elemento el la aro. 

Ekz. por la vorto "malsanulejan_in_o", ek kontroli de signoĉeno parto "malsanulejan", la eltajpota rezulto estu "lsan_ul_ej_an_in_o".

10\. forigu dividilojn, kiuj havas spacon, interjunkcion aŭ novlinio ĉe iu ajn flanko de si, forigi dividilojn, kiuj estas ĉe la komenco aŭ fino de la tuta teksto (dosiero)， anstataŭi 
seninterrompajn plurajn dividilojn per nur unu.

## Prefiksoj (✓programita, sed ni devas rapidigi tion)

11\. de komenco finen kontroli ĉiujn vortojn, pri ĉu ekzistus elementoj ĉe la komenco, havas neniliterojn pli antaŭeajn, estas de la aro {bo,ĉef,dis,ek,eks,ge,mal,mis,pra,re,afro,anti,arĥi,aŭdio,aŭto,bio,des,eko,eŭro,hiper,infra,ko,kver,makro,meta,mikro,mini,mono,pre,proto,pseŭdo,retro,san,semi,stif,tele,termo,ultra,video}. Se tio ekzistas, aldoni la dividilon "\_" post tion, kaj reagadi per antaŭa logiko, ĝis kiam ne ekzistas elemento de la aro.

Ekz. por "geboav_o_j", eltajpota rezulto estu "ge_bo_av_o_j"; por "Maldis_ig_i", eltajpota rezulto estu "Mal_dis_ig_i". Logiko de ĉi tiu paŝo estas simila al antaŭa paŝo pri sufikso, sed la direkto estas inversa, kaj povus prilabori eblecojn kun majuskloj ĉe la unua, tuta aŭ nenia lokoj. la serĉado devas ignori la usklecon, sed ne ŝanĝos la usklon post aldoni dividilojn.

## Radikoj (farota)

12\. Legi la vortaran dosieron "radiko.txt" en la laborloko, por la parto inter enmetiaj dividiloj de la 9-a k la 10-a paŝo, kontroli ĉu tio estas signoĉeno kunmetita de elementoj nur de radiko.txt per iu ajn nombro aŭ vicordo, enmeti dividilon inter ilin; se iu vorto ne estis prilaborita per antaŭaj paŝoj (sen dividilo), ankoraŭ prilabori kiel la meza parto; por la 11-a paŝo, nur enmeti dividilon en tia situacio, kiam 2 partoj da signoĉeno estas ambaŭ de radiko.txt, se male, fari nenion.

(La vortaro estas granda, kaj prilaborota teksto estas ankaŭ granda, do se tio povas pli boniĝi per iu biblioteko, bv proponi al mi, dankon!) :)

Tio estas kontroli ĉu (nur) ekzistas iom da elementoj de radiko.txt per iuj vicordoj kuniĝis nova signoĉeno kaj nur estas inter spacoj, dividiloj aŭ streketoj; ne povas esti ĉia ajn literon aŭ signon inter 2 elementoj; dum la prilaborado, streketo estu rigardata kiel litero.

## Malprilabori vortetojn (farota)

13\. Prilabori listo de vortetoj per antaŭaj paŝoj, kaj anstataŭi la prilaboritaj per originaj

## Dividi tabelvortojn (farota)

14\. anstataŭ [ĉia, ia, kia, nenia, tia, ĉial, ial, kial, nenial, tial, ĉiam, iam, kiam, neniam, tiam, ĉie, ie, kie, nenie, tie, ĉiel, iel, kiel, neniel, tiel, ĉies, ies, kies, nenies, ties, ĉio, io, kio, nenio, tio, ĉiom, iom, kiom, neniom, tiom, ĉiu, iu, kiu, neniu, tiu] per [ĉi_a, i_a, ki_a, neni_a, ti_a, ĉi_al, i_al, ki_al, neni_al, ti_al, ĉi_am, i_am, ki_am, neni_am, ti_am, ĉi_e, i_e, ki_e, neni_e, ti_e, ĉi_el, i_el, ki_el, neni_el, ti_el, ĉi_es, i_es, ki_es, neni_es, ti_es, ĉi_o, i_o, ki_o, neni_o, ti_o, ĉi_om, i_om, ki_om, neni_om, ti_om, ĉi_u, i_u, ki_u, neni_u, ti_u]

Uskleco ne influas la serĉo, sed ne ŝanĝiĝos post antaŭigado

## Malprilabori misdividitajn morfemojn,  
Ekz. "l_um_o", "hor_loĝ_o", "eks_kurs_o" (farota)

Tiu ĉi paŝo povus dismetiĝi inter multaj paŝoj por kontraŭi misagojn.

## Alia aldona pensado (farota, aŭ nur diskutota)

Mi pensis pri tio, ke la mala prilaboro poas okazi ne nur en la fina paŝo, sed multfoje sekvas aliajn misageblajn paŝojn, kaj la funkcio povas uziĝi plurfoje.

Ni povas prilabori liston de morfemoj (la dosiero "vortaro" kaj aldonaj estonte), tiel ni havos anstataŭ-interresponda listo, por eble pli rapida komputo. Ni povas plani speciala funkcio por krei la interreaponda listo per vortaro, do tio povas pli facile generiĝi.

Ni eble (mi ne certas) povas ordigi radikojn per longeco, tiel post kontroli mallongajn radikojn (ekz. "hor" k "loĝ"), ĝi ankoraŭ povas daŭre kontroli la longajn (ekz. "horloĝ")

Ni povas unue nur prilabori tiujn longajn morfemojn, kaj por tro mallongaj (ekz. "-i-"), kontroli poste per pli bonaj rimedoj aŭ manlaboro. 

Ni povas uzi eksterajn vortarojn kiel dosierojn anstataŭ rekte enkodigi la aron en programon, tiel oni povas pli facile novigi la vortaron laŭ bezono.

La programo eble povas fariĝi biblioteko, por pli komplikaj logikoj, aŭ nur uzi parton de la programo. (ekz nur kontroli sekson en iu teksto)

Originigilo povas ankaŭ kreiĝi per ĉi projekto, eble tio ne valoras por establi novan tenejon.
