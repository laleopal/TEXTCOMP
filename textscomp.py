from topfields import allfields
from chunker import better_chunker
import os
import glob
import csv
from relations_news import reldict

ignore = ['Pn', 'Cj']

# Коэффициенты значимости, подобранные по методу линейной регрессии
sum2coeff = [0.44, 0.08, 0.41, 0.03, 0.5, 0.05]

def comparetexts(file1, file2, vd):
    """Counts 6 parameters for texts comparison"""


    # матрица для полностью совпавших предикатов
    pred_all_matrix = []
    # матрица для частично совпавших предикатов
    pred_comp_matrix = []
    # матрица сравнения подлежащих при предикатах
    subj_pred_matrix = []
    # матрица для полностью совпавших подлежащих
    subj_comp_matrix = []
    # матрица сравнения (зависимых) слов в неглавных оп полях - частичные совпадения
    sec_words_matrix = []
    # матрица для полностью совпавших неглавных чанков
    sec_all_matrix = []

    # Представляем оба текста в виде набора предикатов
    file1preds = allfields(better_chunker(file1))
    file2preds = allfields(better_chunker(file2))


    # Сначала строим матрицу по предикатам
    for predind1, predicate1 in enumerate(file1preds):
        predp_line = []
        predc_line = []
        subjp_line = []
        subjc_line = []
        sec_dep_line = []
        sec_all_line = []

        ignp1 = 0
        if predicate1.pred != 'None':
            if predicate1.pred.ml == 'быть':
                ignp1 = 1

        igns1 = 0
        if predicate1.subjfield != 'None':
            if predicate1.subjfield.mw[:2] in ignore:
                igns1 = 1

        for predind2, predicate2 in enumerate(file2preds):

            # Здесь заполняем синтаксич-семантич матрицу предикатов
            ps = 0
            mps = 0
            if predicate1.pred != 'None' and predicate2.pred != 'None':
                if predicate2.pred.ml == 'быть':
                    ignp2 = 1
                else:
                    ignp2 = 0
                p1 = (str(predicate1.pred.ml), str(predicate2.pred.ml))
                p2 = (str(predicate2.pred.ml), str(predicate1.pred.ml))

                if str(predicate1.pred.ml) != 'быть':
                    if str(predicate1.pred.mw) == str(predicate2.pred.mw) and str(predicate1.pred.ml) == str(
                            predicate2.pred.ml) \
                            or p1 in reldict['Synonym'] and str(predicate1.pred.mw) == str(predicate2.pred.mw) \
                            or p2 in reldict['Synonym'] and str(predicate1.pred.mw) == str(predicate2.pred.mw):
                        ps += 1
                    elif str(predicate1.pred.ml) == str(predicate2.pred.ml) \
                            or p1 in reldict['Near_Synonym'] or p2 in reldict['Near_Synonym'] \
                            or p1 in reldict['Synonym'] or p2 in reldict['Synonym'] \
                            or p1 in reldict['Imperfective_aspect'] or p2 in reldict['Imperfective_aspect'] \
                            or p1 in reldict['Perfective_aspect'] or p2 in reldict['Perfective_aspect']:
                        ps += 0.7

                # сравниваем зависимые слова
                wpmass1 = []
                wpmass2 = []
                pgrtags1 = []
                pgrtags2 = []

                igny1 = 0
                igny2 = 0

                for chunk in predicate1.pred.tf:
                    for n, elem in enumerate(chunk.chunk):
                        if chunk.lemmas[n] != predicate1.pred.ml:
                            wpmass1.append(chunk.lemmas[n])
                            pgrtags1.append(elem)
                            if elem[:2] in ignore or chunk.lemmas[n] == 'быть':
                                igny1 += 1
                for chunk in predicate2.pred.tf:
                    for n, elem in enumerate(chunk.chunk):
                        if chunk.lemmas[n] != predicate2.pred.ml:
                            wpmass2.append(chunk.lemmas[n])
                            pgrtags2.append(elem)
                            if elem[:2] in ignore or chunk.lemmas[n] == 'быть':
                                igny2 += 1

                if wpmass1 and wpmass2:
                    if len(wpmass1) >= len(wpmass2):
                        for word in wpmass1:
                            if pgrtags1[wpmass1.index(word)][:2] not in ignore:
                                if word in wpmass2:
                                    # для полного сходства слов
                                    if pgrtags1[wpmass1.index(word)] == pgrtags2[wpmass2.index(word)]:
                                        ps += 0.5
                                    else:
                                        # совпали только леммы
                                        ps += 0.3
                                else:
                                    for word2 in wpmass2:
                                        if (str(word), str(word2)) in reldict['Synonym'] \
                                                or (str(word2), str(word)) in reldict['Synonym'] \
                                                or (str(word), str(word2)) in reldict['Near_Synonym'] \
                                                or (str(word2), str(word)) in reldict['Near_Synonym'] \
                                                or (str(word), str(word2)) in reldict['XPOS_Near_Synonym'] \
                                                or (str(word2), str(word)) in reldict['XPOS_Near_Synonym']:
                                            # для полного сходства синонимов
                                            if pgrtags1[wpmass1.index(word)] == pgrtags2[wpmass2.index(word2)]:
                                                ps += 0.5
                                            else:
                                                # совпали только леммы
                                                ps += 0.3
                    else:
                        for word in wpmass2:
                            if pgrtags2[wpmass2.index(word)][:2] not in ignore:
                                if word in wpmass1:
                                    if pgrtags2[wpmass2.index(word)] == pgrtags1[wpmass1.index(word)]:
                                        ps += 0.5
                                    else:
                                        ps += 0.3
                                else:
                                    for word2 in wpmass1:
                                        if (str(word), str(word2)) in reldict['Synonym'] \
                                                or (str(word2), str(word)) in reldict['Synonym'] \
                                                or (str(word), str(word2)) in reldict['Near_Synonym'] \
                                                or (str(word2), str(word)) in reldict['Near_Synonym'] \
                                                or (str(word), str(word2)) in reldict['XPOS_Near_Synonym'] \
                                                or (str(word2), str(word)) in reldict['XPOS_Near_Synonym']:
                                            # для полного сходства слов
                                            if pgrtags2[wpmass2.index(word)] == pgrtags1[wpmass1.index(word2)]:
                                                ps += 0.5
                                            else:
                                                # совпали только леммы
                                                ps += 0.3
                    if len(wpmass1) + len(wpmass2) + 2 - ignp1 - ignp2 - igny1 - igny2 > 0:
                        ps = round((2 * ps / (len(wpmass1) + len(wpmass2) + 2 - ignp1 - ignp2 - igny1 - igny2)), 2)
                        c = round(2 * (1 + (len(wpmass1) - igny1) * 0.5) / (len(wpmass1) + len(wpmass2) + 2 - ignp1 - ignp2 - igny1 - igny2), 2)
                        mc = round(2 * ((len(wpmass1) - igny1) * 0.5 - 1) / (len(wpmass1) + len(wpmass2) + 2 - ignp1 - ignp2 - igny1 - igny2), 2)
                    else:
                        ps = round((2 * ps / (len(wpmass1) + len(wpmass2) + 2)), 2)
                        c = round(2 * (1 + (len(wpmass1) - igny1) * 0.5) / (len(wpmass1) + len(wpmass2) + 2), 2)
                        mc = round(2 * ((len(wpmass1) - igny1) * 0.5 - 1) / (len(wpmass1) + len(wpmass2) + 2), 2)
                    if ps == c or ps == mc:
                        mps = ps

                if mps > 0:
                    predc_line.append(1)
                    predp_line.append(0)
                elif mps < 0:
                    predc_line.append(-1)
                    predp_line.append(0)
                else:
                    if ps == 1:
                        predc_line.append(ps)
                        predp_line.append(0)
                    else:
                        predp_line.append(ps)
                        predc_line.append(0)
            else:
                predp_line.append(0)
                predc_line.append(0)


            # Здесь заполняем матрицу по подлежащим
            if predicate1.fieldmatrix[2] == predicate2.fieldmatrix[2] == 1:
                cs = 0
                mcs = 0
                s1 = (str(predicate1.subjfield.ml), str(predicate2.subjfield.ml))
                s2 = (str(predicate2.subjfield.ml), str(predicate1.subjfield.ml))
                # сравниваем главные слова (без учета местоимений!!!!!!!!)
                if predicate1.subjfield.mw[:2] != 'Pn':
                    igns2 = 0
                    if str(predicate1.subjfield.mw) == str(predicate2.subjfield.mw) and str(predicate1.subjfield.ml) == str(predicate2.subjfield.ml)\
                            or s1 in reldict['Synonym'] and str(predicate1.subjfield.mw) == str(predicate2.subjfield.mw)\
                            or s2 in reldict['Synonym'] and str(predicate1.subjfield.mw) == str(predicate2.subjfield.mw):
                        cs += 1
                    elif str(predicate1.subjfield.ml) == str(predicate2.subjfield.ml) \
                            or s1 in reldict['Synonym'] or s2 in reldict['Synonym'] \
                            or s1 in reldict['Near_Synonym'] or s2 in reldict['Near_Synonym']:
                        cs += 0.7
                else:
                    igns2 = 1

                # сравниваем зависимые слова
                wordmass1 = []
                wordmass2 = []
                grtags1 = []
                grtags2 = []

                ignz1 = 0
                ignz2 = 0

                for chunk in predicate1.subjfield.tf:
                    for n, elem in enumerate(chunk.chunk):
                        if chunk.lemmas[n] != predicate1.subjfield.ml:
                            wordmass1.append(chunk.lemmas[n])
                            grtags1.append(elem)
                            if elem[:2] in ignore or chunk.lemmas[n] == 'быть':
                                ignz1 += 1

                for chunk in predicate2.subjfield.tf:
                    for n, elem in enumerate(chunk.chunk):
                        if chunk.lemmas[n] != predicate2.subjfield.ml:
                            wordmass2.append(chunk.lemmas[n])
                            grtags2.append(elem)
                            if elem[:2] in ignore or chunk.lemmas[n] == 'быть':
                                ignz2 += 1

                if wordmass1 and wordmass2:
                    if len(wordmass1) >= len(wordmass2):
                        for word in wordmass1:
                            if grtags1[wordmass1.index(word)][:2] not in ignore:
                                if word in wordmass2:
                                    # для полного сходства слов
                                    if grtags1[wordmass1.index(word)] == grtags2[wordmass2.index(word)]:
                                        cs += 0.5
                                    else:
                                        # совпали только леммы
                                        cs += 0.3

                                else:
                                    for word2 in wordmass2:
                                        if (str(word), str(word2)) in reldict['Synonym'] \
                                           or (str(word2), str(word)) in reldict['Synonym']\
                                           or (str(word), str(word2)) in reldict['Near_Synonym']\
                                           or (str(word2), str(word)) in reldict['Near_Synonym']\
                                           or (str(word), str(word2)) in reldict['XPOS_Near_Synonym']\
                                           or (str(word2), str(word)) in reldict['XPOS_Near_Synonym']:
                                            # для полного сходства синонимов
                                            if grtags1[wordmass1.index(word)] == grtags2[wordmass2.index(word2)]:
                                                cs += 0.5
                                            else:
                                                # совпали только леммы
                                                cs += 0.3
                    else:
                        for word in wordmass2:
                            if grtags2[wordmass2.index(word)][:2] not in ignore:
                                if word in wordmass1:
                                    if grtags2[wordmass2.index(word)] == grtags1[wordmass1.index(word)]:
                                        cs += 0.5
                                    else:
                                        cs += 0.3
                                else:
                                    for word2 in wordmass1:
                                        if (str(word), str(word2)) in reldict['Synonym'] \
                                           or (str(word2), str(word)) in reldict['Synonym']\
                                           or (str(word), str(word2)) in reldict['Near_Synonym']\
                                           or (str(word2), str(word)) in reldict['Near_Synonym']\
                                           or (str(word), str(word2)) in reldict['XPOS_Near_Synonym']\
                                           or (str(word2), str(word)) in reldict['XPOS_Near_Synonym']:
                                            # для полного сходства слов
                                            if grtags2[wordmass2.index(word)] == grtags1[wordmass1.index(word2)]:
                                                cs += 0.5
                                            else:
                                                # совпали только леммы
                                                cs += 0.3


                    if len(wordmass1) + len(wordmass2) + 2 - igns1 - igns2 - ignz1 - ignz2 > 0:
                        cs = round((2 * cs / (len(wordmass1) + len(wordmass2) + 2 - igns1 - igns2 - ignz1 - ignz2)), 2)
                        c = round(2 * (1 + (len(wordmass1) - ignz1) * 0.5) / (len(wordmass1) + len(wordmass2) + 2 - igns1 - igns2 - ignz1 - ignz2), 2)
                    else:
                        cs = round((2 * cs / (len(wordmass1) + len(wordmass2) + 2)), 2)
                        c = round(2 * (1 + (len(wordmass1) - ignz1) * 0.5) / (len(wordmass1) + len(wordmass2) + 2), 2)

                    if cs == c:
                        mcs = cs

                if mcs != 0:
                    subjc_line.append(1)
                    subjp_line.append(0)
                else:
                    if cs == 1:
                        subjc_line.append(cs)
                        subjp_line.append(0)
                    else:
                        subjp_line.append(cs)
                        subjc_line.append(0)
            else:
                subjp_line.append(0)
                subjc_line.append(0)



            # Матрица предикатов по чанкам полей распространителей
            chunksinfields = {}
            mwinfields = {}
            mwignoreict = {}
            # залезаем в массив полей первого предиката и перебираем чанки в каждом поле
            for fieldindex1, field1 in enumerate(predicate1.fields):
                depqch = 0

                for chunkindex1, chunk1 in enumerate(field1.tf):

                    mlemma1 = str(chunk1.main_lemma)


                    ign_number = 0
                    for i, word in enumerate(chunk1.chunk):
                        if word[:2] in ignore or chunk1.lemmas[i] == 'быть':
                            ign_number += 1

                    # сравниваем их со всеми чанками всех полей второго предиката
                    mw2ignore = {}
                    for fieldindex2, field2 in enumerate(predicate2.fields):
                        mweqch = 0
                        ign = 0
                        chunkindex2 = 0

                        if field1.name == 'NomNoun' and 'NomNoun' == field2.name\
                                or field1.name == 'FinVerb' and 'FinVerb' == field2.name:
                            pass
                        else:
                            for chunk2 in field2.tf:
                                ign_2_number = 0
                                for i, word in enumerate(chunk2.chunk):
                                    if word[:2] in ignore or chunk2.lemmas[i] == 'быть':
                                        ign_2_number += 1
                                if chunk2.main_word[:2] in ignore or chunk2.main_lemma == 'быть':
                                    if fieldindex2 in mw2ignore:
                                        mw2ignore[fieldindex2] += 1
                                    else:
                                        mw2ignore[fieldindex2] = 1
                                chunkindex2 += 1
                                ch1 = (str(chunk1.main_lemma), str(chunk2.main_lemma))
                                ch2 = (str(chunk2.main_lemma), str(chunk1.main_lemma))
                                # сравниваем главные слова в чанках
                                if chunk1.main_word[:2] not in ignore and str(chunk1.main_lemma) != 'быть':
                                    if str(chunk1.main_word) == str(chunk2.main_word) and mlemma1 == str(chunk2.main_lemma)\
                                            or ch1 in reldict['Synonym'] and str(chunk1.main_word) == str(chunk2.main_word)\
                                            or ch2 in reldict['Synonym'] and str(chunk1.main_word) == str(chunk2.main_word):
                                        mweqch += 1
                                    elif str(chunk1.main_lemma) == str(chunk2.main_lemma) \
                                            or ch1 in reldict['Synonym'] or ch2 in reldict['Synonym'] \
                                            or ch1 in reldict['Near_Synonym'] or ch2 in reldict['Near_Synonym'] \
                                            or ch1 in reldict['XPOS_Near_Synonym'] or ch2 in reldict['XPOS_Near_Synonym'] \
                                            or ch1 in reldict['Imperfective_aspect'] or ch2 in reldict['Imperfective_aspect']\
                                            or ch1 in reldict['Perfective_aspect'] or ch2 in reldict['Perfective_aspect']:
                                        mweqch += 0.7
                                else:
                                    ign += 1

                                chscr = 0

                                # сравниваем зависимые слова чанков
                                for m1, elem1 in enumerate(chunk1.chunk):
                                    lemma1 = chunk1.lemmas[m1]
                                    for m2, elem2 in enumerate(chunk2.chunk):
                                        d1 = (str(lemma1), str(chunk2.lemmas[m2]))
                                        d2 = (str(chunk2.lemmas[m2]), str(lemma1))
                                        if lemma1 == chunk1.main_lemma and chunk2.lemmas[m2] == chunk2.main_lemma:
                                            pass
                                        elif chunk1.chunk[m1][:2] not in ignore and str(lemma1) != 'быть':
                                            if elem1 == elem2 and lemma1 == chunk2.lemmas[m2]\
                                                    or elem1 == elem2 and d1 in reldict['Synonym']\
                                                    or elem1 == elem2 and d2 in reldict['Synonym']:
                                                chscr += 0.5
                                            elif lemma1 == chunk2.lemmas[m2]\
                                                    or d1 in reldict['Synonym'] or d2 in reldict['Synonym'] \
                                                    or d1 in reldict['Near_Synonym'] or d2 in reldict['Near_Synonym'] \
                                                    or d1 in reldict['XPOS_Near_Synonym'] or d2 in reldict['XPOS_Near_Synonym'] \
                                                    or d1 in reldict['Imperfective_aspect'] or d2 in reldict['Imperfective_aspect'] \
                                                    or d1 in reldict['Perfective_aspect'] or d2 in reldict['Perfective_aspect']:
                                                chscr += 0.3

                                if len(chunk1.chunk) + len(chunk2.chunk) - 2 - ign_number - ign_2_number > 0:
                                    sec_words_sc = round(2 * chscr / (len(chunk1.chunk) + len(chunk2.chunk) - 2 - ign_number - ign_2_number), 2)
                                else:
                                    sec_words_sc = round(chscr, 2)
                                depqch += sec_words_sc
                                if sec_words_sc > 0:
                                    if (fieldindex1, fieldindex2) in chunksinfields:
                                        chunksinfields[(fieldindex1, fieldindex2)] += sec_words_sc
                                    else:
                                        chunksinfields[(fieldindex1, fieldindex2)] = sec_words_sc

                        if mweqch > 0:
                            if (fieldindex1, fieldindex2) in mwinfields:
                                mwinfields[(fieldindex1, fieldindex2)] += mweqch
                            else:
                                mwinfields[(fieldindex1, fieldindex2)] = mweqch



            dwscore = 0
            mwscore = 0
            for key in chunksinfields:
                vl = chunksinfields[key]
                dwscore += round(2*vl/(predicate1.fields[key[0]].vol + predicate2.fields[key[1]].vol), 2)
            for key in mwinfields:
                k = mwinfields[key]
                i1 = 0
                i2 = 0
                if key[0] in mwignoreict:
                    i1 = mwignoreict[key[0]]
                if key[1] in mw2ignore:
                    i2 = mw2ignore[key[1]]

                if predicate1.fields[key[0]].vol + predicate2.fields[key[1]].vol - i1 - i2 > 0:
                    mwscore += round(2*k/(predicate1.fields[key[0]].vol + predicate2.fields[key[1]].vol - i1 - i2), 2)

            v = predicate1.fieldmatrix[2]+predicate1.fieldmatrix[4]+predicate2.fieldmatrix[2]+predicate2.fieldmatrix[4]
            if (len(predicate1.fields) + len(predicate2.fields) - v) > 0:
                mwscore = round((2 * mwscore / (len(predicate1.fields) + len(predicate2.fields) - v)), 2)
                dwscore = round((2 * dwscore/ (len(predicate1.fields) + len(predicate2.fields) - v)), 2)
            else:
                dwscore = round(2 * dwscore / (len(predicate1.fields) + len(predicate2.fields)), 2)
                mwscore = round(2 * mwscore / (len(predicate1.fields) + len(predicate2.fields)), 2)

            if mwscore == dwscore == 0:
                sec_dep_line.append(dwscore + mwscore)
                sec_all_line.append(0)
            else:
                if mwscore == predicate1.ideal_secmainw and dwscore == predicate1.ideal_sc_w:
                    sec_all_line.append(1)
                    sec_dep_line.append(0)
                else:
                    sec_dep_line.append(dwscore+mwscore)
                    sec_all_line.append(0)


        pred_all_matrix.append(predc_line)
        pred_comp_matrix.append(predp_line)
        subj_pred_matrix.append(subjp_line)
        subj_comp_matrix.append(subjc_line)
        sec_words_matrix.append(sec_dep_line)
        sec_all_matrix.append(sec_all_line)


    # Предикаты: х1 - полное совпадение чанков, х2 - частичное
    x1 = 0
    x2 = 0

    # Подлежащие: х3 - полное совпадение чанков, х4 - частичное
    x3 = 0
    x4 = 0

    # параметры для главных слов неглавных чанков (x5 - полное совпадение, x6 - частичное)
    x5 = 0
    x6 = 0

    p = round(2 / (len(file1preds) + len(file2preds)), 2)

    for line in pred_all_matrix:
        for el in line:
            x1+=el
    for line in pred_comp_matrix:
        for el in line:
            x2 += el
    x2 = round(x2, 2)
    for line in subj_comp_matrix:
        for el in line:
            x3 += el
    for line in subj_pred_matrix:
        for t in line:
            x4 += t
    x4 = round(x4, 2)
    for line in sec_all_matrix:
        for el in line:
            x5 += el
    for line in sec_words_matrix:
        for el in line:
            x6 += el
    x5 = round(x5, 2)
    x6 = round(x6, 2)

    if p != 0:
        x1 = round(x1*p, 2)
        x2 = round(x2*p, 2)
        x3 = round(x3*p, 2)
        x4 = round(x4*p, 2)
        x5 = round(x5*p, 2)
        x6 = round(x6*p, 2)
    mtx = str(file1) + ' & ' + str(file2)
    vd[mtx] = (x1, x2, x3, x4, x5, x6)

    return mtx


def alltexts(dir):
    vd = {}
    cd = os.getcwd()
    os.chdir(dir)
    alltxt = glob.glob('*.xml')
    for ind, file in enumerate(alltxt):
        for nextfile in alltxt[ind:]:
            comparetexts(file, nextfile, vd)
    os.chdir(cd)
    return vd


def cnt(coeff, data):
    result = 0
    for i in range(6):
        result += coeff[i]*data[i]
    result = round(result, 2)
    if result > 0.8:
        result = 1
    return result


def getall(coeff, dir, quant):
    """Считает показатели сходства текстов друг с другом, выдает матрицу, в которой эти оценки записаны.
    coeff - коэффициенты значимости
    dir - директория, в коорой находятся тексты для сравнения (папка inpt)
    quant - количество сравниваемых текстов
    """
    matrix = []
    mline = []
    for i in range(quant):
        mline.append(0)
    for i in range(quant):
        matrix.append([0]*quant)

    print('Please, be patient. The algorithm is running...')

    simdict ={}
    prevv = ''
    mtrxln = 0
    mtrxcl = 0
    allvd = alltexts(dir)
    for key in sorted(allvd):
        simdict[key] = cnt(coeff, allvd[key])
        crell = key[:key.index('&')]
        if crell != prevv and prevv != '':
            mtrxln += 1
            mtrxcl = mtrxln
        matrix[mtrxln].pop(mtrxcl)
        matrix[mtrxln].insert(mtrxcl, simdict[key])
        prevv = crell
        mtrxcl += 1
    os.chdir(os.getcwd() + '\\otpt')
    with open('result.csv', mode = 'w', encoding = 'utf-8', newline='') as nmb:
        wr = csv.writer(nmb, delimiter = ';')
        for line in matrix:
            wr.writerow(line)

    return simdict





if __name__ == '__main__':
    #comparetexts('dc_lenta_01.xml', 'dc_freedom_04.xml', vd)
    getall(sum2coeff, os.getcwd() + '\\inpt', 3)