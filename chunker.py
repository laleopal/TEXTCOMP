from xml.etree import ElementTree as ET
from goldch import gold

gold = list(gold)
gold.sort(key=lambda x: (-len(x), x[0]))

class Chunks:
    def __init__(self, tpl):
        self.chunk = tpl
        self.length = len(tpl)
        self.lemmas = []

    def __repr__(self):
        return  "%s     %s" % (str(self.chunk), str(self.lemmas))

    #Обобщающая ф-ия для выделения главных членов без доп условий
    def mw(self, tag):
        for elm in self.chunk:
            if elm[:2] == tag:
                return elm

    #Ф-ия для двух тегов (сущ/мест и прич)
    def mw2tgs(self, tg1, tg2):
        tg1pos = ''
        tg2pos = []
        for ty in self.chunk:
            if ty[:2] == tg1:
                tg1pos = ty
            elif ty[:2] == tg2:
                tg2pos.append(ty)
        bb = 0
        rt = ''
        for n in tg2pos:
            if tg1pos[4:15] == n[4:15]:
                bb += 1
                rt = n
                break
        if bb == 0:
            rt = tg1pos
        return rt

    # Возвращает главное слово в чанке
    @property
    def main_word(self):
        themainword = ""
        if self.length == 1:
            themainword = self.chunk[0]
        else:
            pos = {fl[:2] for fl in self.chunk}
            posmn = {'Vb', 'Dp', 'Vp', 'Pd', 'Ap', 'Cm'} & pos
            posadj = {'Aj', 'Ad', 'Cj', 'Nu'} & pos
            # Проверяем, есть ли в чанке глагол/дееприч/краткое прич
            if posmn:
                themainword = self.mw(list(posmn)[0])


            elif 'Nn' in pos and 'Pt' in pos:
                themainword = self.mw2tgs('Pt', 'Nn')
            elif 'Pn' in pos and 'Pt' in pos:
                themainword = self.mw2tgs('Pt', 'Pn')

            elif 'Nn' in pos:
                nnlist = []
                g=0
                for u in self.chunk:
                    if u[:2] == 'Nn':
                        if u[5:7] == 'Nm':
                            g+=1
                            themainword = u
                            break
                        nnlist.append(u)
                if g==0:
                    themainword = nnlist[0]

            elif 'Pn' in pos:
                nnlist = []
                for u in self.chunk:
                    if u[:2] == 'Pn':
                        if u[5:7] == 'Nm':
                            themainword = u
                            break
                        nnlist.append(u)
                if nnlist:
                    themainword = nnlist[0]

            elif 'Nu' in pos:
                nnlist = []
                for u in self.chunk:
                    if u[:2] == 'Nu':
                        themainword = u
                        nnlist.append(u)
                if nnlist:
                    themainword = nnlist[0]

            elif 'Pt' in pos:
                nnlist = []
                for u in self.chunk:
                    if u[:2] == 'Pt':
                        themainword = u
                        nnlist.append(u)
                if nnlist:
                    themainword = nnlist[0]

            elif posadj:
                themainword = self.mw(list(posadj)[0])


            else:
                themainword = self.chunk[0]

        return themainword

    # Возвращает главную лемму
    @property
    def main_lemma(self):
        i = 0
        for fr, elem in enumerate(self.chunk):
            if elem == self.main_word:
                i = fr
                break
        return (self.lemmas[self.chunk.index(self.main_word)])

    def ideal_secwords_score(self):
        ign_number = 0
        for n, t in enumerate(self.chunk):
            if t[:2] in ['Pn', 'Cj'] and self.lemmas[n] != self.main_lemma or self.lemmas[n] == 'быть' and self.lemmas[n] != self.main_lemma:
                ign_number += 1
        if 2 * (self.length - ign_number) - 2 > 0:
            return round((self.length - 1 - ign_number) / (2 * (self.length - ign_number) - 2), 2)
        else:
            return 0


def generate_chunks(gld, crrntcnk, oddchunks):
    """Divides text bits into chunks based on a list of "gold" chunks.
        Yields chunks.
        @gld - list of gold chunks
        @crrntcnk - text bit in question
        @oddchunks - set for words/phrases that are in the text but not in the gold list"""

    checkval = 0

    # Берем строку из списка золотых чанков (равную или меньшую по длине, чем данный кусок текста)
    for gch in gld:
        lengch = len(gch)
        if lengch <= crrntcnk.length:
            newchunk = []

            # Поэлементно сравниваем ее с куском текста
            for i, gldch in enumerate(gch):
                if gldch == crrntcnk.chunk[i]:
                    newchunk.append(gldch)

            # Если мы нашли золотой чанк, то выдаем его и движемся дальше
            if len(newchunk) == lengch and checkval == 0:

                # Выдаем "незолотой" чанк перед найденным чанком (если таковой имеется)
                if oddchunks:
                    och = Chunks(tuple(oddchunks))
                    och.lemmas = crrntcnk.lemmas[:len(oddchunks)]
                    crrntcnk.lemmas = crrntcnk.lemmas[len(oddchunks):]
                    yield och
                    oddchunks.clear()

                nch = Chunks(tuple(newchunk))
                nch.lemmas = crrntcnk.lemmas[:lengch]
                yield nch
                checkval += 1

                # Если еще остался неразобранный кусок текста, разбираем его
                if len(crrntcnk.chunk) > lengch:
                    cutlemmas = crrntcnk.lemmas[lengch:]
                    crrntcnk = Chunks(crrntcnk.chunk[lengch:])
                    crrntcnk.lemmas = cutlemmas
                    yield from generate_chunks(gold, crrntcnk, oddchunks)
                    break

    # Если в золотом списке чанков нет похожего на данный, то добавляем первое слово в список исключений
    if checkval == 0:
        ll = crrntcnk.lemmas
        oddchunks.append(crrntcnk.chunk[0])

        # Если кусок текста не закончился, продолжаем в нем поиск чанков
        if crrntcnk.length > 1:
            crrntcnk = Chunks(crrntcnk.chunk[1:])
            crrntcnk.lemmas = ll
            yield from generate_chunks(gold, crrntcnk, oddchunks)
        else:
            och = Chunks(tuple(oddchunks))
            och.lemmas = crrntcnk.lemmas[:len(oddchunks)]
            yield och


def dumb_chunker(file):
    """Splits text bits into chunks from one terminal punctuation mark to the next one.
        Returns list of chunks.
        @file - text to be divided"""
    tree = ET.parse(file)
    root = tree.getroot()
    finmass = []
    chunk = []
    lemmas = []

    for child in root:
        for element in child:
            # берем только слова, зп не запоминаем!
            if element.tag == 'w':
                chunk.append(element.get("ana"))
                lemmas.append(element.get("lemma"))
            if element.get("ana") == "PM,Tr,_" and element.get("lemma") != "," and len(chunk) > 0:
                cnk = Chunks(tuple(chunk))
                for lm in lemmas:
                    cnk.lemmas.append(lm)
                finmass.append(cnk)
                chunk.clear()
                lemmas.clear()

    """for i in finmass:
        print(i)
        print(i.lemmas)"""
    return finmass

def better_chunker(file):
    dch = dumb_chunker(file)
    betterchunks = []

    # Разбиваем каждое предложение на чанки
    for dc in dch:
        sentencechunks = []
        for m in generate_chunks(gold, dc, []):
            sentencechunks.append(m)
        betterchunks.append(sentencechunks)

    # Корректируем полученные чанки
    for sch in betterchunks:
        for ind, echunk in enumerate(sch):
            if ind+1 < len(sch)-1:
                nxtchunk = sch[ind+1]
                nxtchmass = list(nxtchunk.chunk)
                nmw = nxtchunk.main_word
                ech = list(echunk.chunk)
                if echunk.length ==1:
                    if ech == ['Pp'] or ech == ['Pc'] and echunk.lemmas[0] in ('ни', 'не', 'на') \
                            or ech[0][:2] == 'Aj' and nmw[:2] == 'Nn' and ech[0][5:10] in (nmw[5:10], nmw[6:11]) \
                            or ech == ['Ad'] and nmw[:2] == 'Vb': # and echunk.lemmas != ['что']
                        nxtchunk2 = sch[ind + 2]
                        nw2 = nxtchunk2.main_word
                        for tpe in nxtchunk.chunk:
                           ech.append(tpe)
                        ulmms = echunk.lemmas
                        for lme in nxtchunk.lemmas:
                            ulmms.append(lme)

                        if nxtchunk.main_word[:2] in ('Nn', 'Nu', 'Pn') and nw2[:7] == 'Nn,_,Gn' \
                            or ech[-1][:2] == 'Aj' and nxtchunk2.chunk[0][:2] == 'Nn' and ech[-1][5:10] in (nxtchunk2.chunk[0][5:10], nxtchunk2.chunk[0][6:11]) \
                                or ech[-1] == 'Pp' and nxtchunk2.chunk[0][:2] == 'Nn':
                            for tp in nxtchunk2.chunk:
                                ech.append(tp)
                            for lm in nxtchunk2.lemmas:
                                ulmms.append(lm)
                            sch.pop(ind+2)

                        unitedchunk = Chunks(tuple(ech))
                        unitedchunk.lemmas = ulmms
                        sch.pop(ind+1)
                        sch.pop(ind)
                        sch.insert(ind, unitedchunk)

                elif echunk.main_word[:2] in ('Nn', 'Nu', 'Pn') and nmw[:7] == 'Nn,_,Gn' \
                        or echunk.main_word[:2] == 'Ad' and nmw[:2] == 'Ad':
                    for tpe in nxtchunk.chunk:
                        ech.append(tpe)
                    unitedchunk = Chunks(tuple(ech))
                    unitedchunk.lemmas = echunk.lemmas
                    for lme in nxtchunk.lemmas:
                        unitedchunk.lemmas.append(lme)
                    sch.pop(ind + 1)
                    sch.pop(ind)
                    sch.insert(ind, unitedchunk)

                elif ech[-1][:2] == 'Aj' and nxtchmass[0][:2] == 'Nn' and ech[-1][5:10] in (nxtchmass[0][5:10], nxtchmass[0][6:11]) \
                        or ech[-1] == 'Pp' and nxtchmass[0][:2] == 'Nn':
                    for tpe in nxtchunk.chunk:
                        ech.append(tpe)
                    unitedchunk = Chunks(tuple(ech))
                    unitedchunk.lemmas = echunk.lemmas
                    for lme in nxtchunk.lemmas:
                        unitedchunk.lemmas.append(lme)
                    sch.pop(ind + 1)
                    sch.pop(ind)
                    sch.insert(ind, unitedchunk)

    return betterchunks


if __name__ == '__main__':
    better_chunker("el_liberals_01.xml")