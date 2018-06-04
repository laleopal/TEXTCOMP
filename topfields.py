from chunker import better_chunker
from generatemininds import generatenumbers
from conj import sing

class Predicate:
    def __init__(self, predicate, sentind, fieldmass, fieldmatrix):
        self.pred = predicate
        self.sentind = sentind
        self.fields = fieldmass
        self.fieldmatrix = fieldmatrix

        if self.fieldmatrix[2] ==1:
            for field in self.fields:
                if field.name == 'NomNoun':
                    self.subjfield = field
        else:
            self.subjfield = 'None'


        self.ideal_sc_w = 0
        ign = self.fieldmatrix[2] + self.fieldmatrix[4]
        self.ideal_secmainw = 0
        for f in self.fields:
            if f.name != 'NomNoun' and f.name != 'FinVerb':
                self.ideal_sc_w += f.ideal_secwords_fieldsc
                self.ideal_secmainw += f.smw
        if len(self.fields) - ign > 0:
            self.ideal_sc_w = round(self.ideal_sc_w/(len(self.fields) - ign), 2)
            self.ideal_secmainw = round(self.ideal_secmainw/(len(self.fields) - ign), 2)
        else:
            self.ideal_sc_w = 0
            self.ideal_secmainw = 0

    def __repr__(self):
        if self.pred == 'None':
            return self.pred
        else:
            return '%s  %s' %(self.pred.mw, self.pred.ml)


class TopField:
    def __init__(self, chunkmass):
        self.tf = chunkmass
        self.vol = len(chunkmass)
        self.lemmas = []

        self.ideal_secwords_fieldsc = 0
        self.smw = 0

        ign = 0
        for chunk in chunkmass:
            self.lemmas.append(chunk.lemmas)
            self.ideal_secwords_fieldsc += chunk.ideal_secwords_score()
            if chunk.main_lemma != 'быть' and chunk.main_word[:2] not in ('Pn', 'Cj'):
                self.smw += 1
            else:
                ign += 1
        self.ideal_secwords_fieldsc = round(self.ideal_secwords_fieldsc/self.vol, 2)
        if self.vol - ign > 0:
            self.smw = round(self.smw/(self.vol -ign), 2)
        else:
            self.smw = 0

    def __repr__(self):
        if hasattr(self, 'name'):
            return '%s \n [ %s ]' % (self.name, '\n'.join(str(chunk) for chunk in self.tf))
        else:
            return '[ %s ]' % '\n'.join(str(chunk) for chunk in self.tf)

class FVField(TopField):
    name = 'FinVerb'
    mtrx_of_flds = []

    @property
    def mw(self):
        for chunk in self.tf:
            if chunk.main_word[:2] in {'Vb', 'Dp', 'Vp', 'Pd', 'Ap'}:
                return chunk.main_word

    @property
    def ml(self):
        for chunk in self.tf:
            if chunk.main_word[:2] in {'Vb', 'Dp', 'Vp', 'Pd', 'Ap'}:
                return chunk.main_lemma

class NNField(TopField):
    name = 'NomNoun'
    @property
    def mw(self):
        for chunk in self.tf:
            if chunk.main_word[:2] in {'Nn', 'Pn'}:
                return chunk.main_word
    @property
    def ml(self):
        for chunk in self.tf:
            if chunk.main_word[:2] in {'Nn', 'Pn'}:
                return chunk.main_lemma

class FDField(TopField):
    name = 'FreeDet'

class RRField(TopField):
    name = 'RightRem'

class LNField(TopField):
    name = 'LeftNounRem'

class CField(TopField):
    name = 'Coordination'

class UKField(TopField):
    name = 'UnableToDefine'

# Порядок представления полей в матрице: Coord, LNRem, NN, FD, FV, RR, U

btset2 = better_chunker('el_liberals_01.xml')

# Объединяет чанки в топологические поля (на уровне предложения)
def gettopfield(chunkedsent, sentind):
    predind = []
    subjind = []
    crdind = []
    fieldsmass = []
    fields_matrix_synt = []
    predicate_collection = []
    for ind, chunk in enumerate(chunkedsent):
        mw = chunk.main_word
        if mw[:2] in ('Vb', 'Vp', 'Pd', 'Ap'):
            predind.append(ind)
        elif mw[:2] in ('Nn', 'Pn') and 'Nm' in (mw[5:7], mw[6:8]):
            subjind.append(ind)
        elif mw[:2] == 'Cj' and chunk.lemmas[0] in sing:
            crdind.append(ind)

    sequence = list(generatenumbers([subjind, predind, crdind]))
    if sequence:
        ln = 0
        lnn = 0
        cr = 0
        nn = 0
        fd = 0
        rr = 0
        next_pred_fieldmass = []
        for nb, ind in enumerate(sequence):
            sub = []
            # Если перед нами ПОДЛЕЖАЩЕЕ
            if ind in subjind:
                # запоминаем его для следующего предиката
                nn +=1
                # Если в списке это превый элемент, но в предложении перед ним есть еще что-то
                if ind > 0 and nb == 0:
                    fieldsmass.append(LNField(chunkedsent[:ind]))
                    next_pred_fieldmass.append(LNField(chunkedsent[:ind]))
                    lnn += 1
                sub.append(chunkedsent[ind])
                fieldsmass.append(NNField(sub))
                next_pred_fieldmass.append(NNField(sub))
                # если между текущим эл-том и следующим есть какие-то чанки
                if nb+1 < len(sequence) and sequence[nb+1]-ind > 1:
                    # следующий эл-т сказуемое
                    if sequence[nb+1] in predind:
                        fieldsmass[-1].pair = chunkedsent[sequence[nb+1]]
                        fieldsmass.append(FDField(chunkedsent[ind + 1:sequence[nb+1]]))
                        # запоминаем для него поля
                        next_pred_fieldmass.append(FDField(chunkedsent[ind + 1:sequence[nb+1]]))
                        fd += 1
                    # следующий эл-т - союз
                    elif sequence[nb+1] in crdind:
                        fieldsmass.append(RRField(chunkedsent[ind + 1:]))
                        rr +=1
                    # следующий эл-т - подлеж
                    else:
                        # если текущий рассматриваемый эл-т первый в списке или перед ним сказуемое с подлежащим, добавляем ему мнимый предикат
                        if nb == 0 \
                                or nb > 0 and sequence[nb - 1] in predind and predicate_collection[-1].fieldmatrix[2] == 1:
                            mt_line_synt = [0] * 7
                            mt_line_synt.pop(2)
                            mt_line_synt.insert(2, 1)
                            nn = 0
                            if lnn >= 1:
                                mt_line_synt.pop(1)
                                mt_line_synt.insert(1, 1)
                                lnn = 0
                            if fd >= 1:
                                mt_line_synt.pop(3)
                                mt_line_synt.insert(3, 1)
                                fd = 0
                            if rr >= 1:
                                mt_line_synt.pop(5)
                                mt_line_synt.insert(5, 1)
                                rr = 0
                            if cr >= 1:
                                mt_line_synt.pop(0)
                                mt_line_synt.insert(0, 1)
                                cr = 0
                            fields_matrix_synt.append(mt_line_synt)
                            fic_pred = Predicate('None', sentind, next_pred_fieldmass, mt_line_synt)
                            next_pred_fieldmass = []
                            predicate_collection.append(fic_pred)
                        # Если текущий эл-т в списке не первый, а перед ним сказуемое без подлежащего
                        elif nb > 0 and sequence[nb - 1] in predind and predicate_collection[-1].fieldmatrix[2] == 0:
                            prevv = predicate_collection[-1]
                            mt_line_synt = predicate_collection[-1].fieldmatrix
                            mt_line_synt.pop(2)
                            mt_line_synt.insert(2, 1)
                            nn = 0
                            if lnn >= 1:
                                mt_line_synt.pop(1)
                                mt_line_synt.insert(1, 1)
                                lnn = 0
                            if fd >= 1:
                                mt_line_synt.pop(3)
                                mt_line_synt.insert(3, 1)
                                fd = 0
                            if rr >= 1:
                                mt_line_synt.pop(5)
                                mt_line_synt.insert(5, 1)
                                rr = 0
                            for el in next_pred_fieldmass:
                                prevv.fields.append(el)
                            mod_pred = Predicate(prevv.pred, sentind, prevv.fields, mt_line_synt)
                            predicate_collection.pop(-1)
                            predicate_collection.append(mod_pred)
                        fieldsmass.append(LNField(chunkedsent[ind + 1:sequence[nb + 1]]))
                        next_pred_fieldmass = []
                        next_pred_fieldmass.append((LNField(chunkedsent[ind + 1:sequence[nb + 1]])))
                        lnn += 1
                # Если предыдущий эл-т из списка - сказуемое, и у него нет подлежащего, приписываем ему это
                # а еще тут условие на то, что текущий эл-т в списке поседний, но в предл после него еще что-то есть
                elif nb > 0 and sequence[nb - 1] in predind and predicate_collection[-1].fieldmatrix[2] == 0 and nb + 1 >= len(sequence) and ind + 1 < len(chunkedsent):
                    fieldsmass.append(RRField(chunkedsent[ind + 1:]))
                    next_pred_fieldmass.append(RRField(chunkedsent[ind + 1:]))
                    rr += 1
                    prevv = predicate_collection[-1]
                    mt_line_synt = predicate_collection[-1].fieldmatrix
                    mt_line_synt.pop(2)
                    mt_line_synt.insert(2, 1)
                    nn = 0
                    if lnn >= 1:
                        mt_line_synt.pop(1)
                        mt_line_synt.insert(1, 1)
                        lnn = 0
                    if fd >= 1:
                        mt_line_synt.pop(3)
                        mt_line_synt.insert(3, 1)
                        fd = 0
                    if rr >= 1:
                        mt_line_synt.pop(5)
                        mt_line_synt.insert(5, 1)
                        rr = 0
                    for el in next_pred_fieldmass:
                        prevv.fields.append(el)
                    mod_pred = Predicate(prevv.pred, sentind, prevv.fields, mt_line_synt)
                    predicate_collection.pop(-1)
                    predicate_collection.append(mod_pred)
                # Если текущий эл-т просто не последний в предложении
                elif nb+1 >= len(sequence) and ind+1 < len(chunkedsent):
                    fieldsmass.append(RRField(chunkedsent[ind+1:]))
                    mt_line_synt = [0] * 7
                    mt_line_synt.pop(2)
                    mt_line_synt.insert(2, 1)
                    nn = 0
                    if lnn >= 1:
                        mt_line_synt.pop(1)
                        mt_line_synt.insert(1, 1)
                        lnn = 0
                    if fd >= 1:
                        mt_line_synt.pop(3)
                        mt_line_synt.insert(3, 1)
                        fd = 0
                    if rr >= 1:
                        mt_line_synt.pop(5)
                        mt_line_synt.insert(5, 1)
                        rr = 0
                    next_pred_fieldmass.append(RRField(chunkedsent[ind+1:]))
                    fic_pred = Predicate('None', sentind, next_pred_fieldmass, mt_line_synt)
                    predicate_collection.append(fic_pred)
                # Если предыдущий эл-т из списка - сказуемое без подлежащего, а текущий последний в предложении вообще
                elif nb > 0 and sequence[nb-1] in predind and predicate_collection[-1].fieldmatrix[2] == 0 and ind+1 >= len(chunkedsent):
                    prevv = predicate_collection[-1]
                    mt_line_synt = predicate_collection[-1].fieldmatrix
                    mt_line_synt.pop(2)
                    mt_line_synt.insert(2, 1)
                    nn = 0
                    if lnn >= 1:
                        mt_line_synt.pop(1)
                        mt_line_synt.insert(1, 1)
                        lnn = 0
                    if fd >= 1:
                        mt_line_synt.pop(3)
                        mt_line_synt.insert(3, 1)
                        fd = 0
                    if rr >= 1:
                        mt_line_synt.pop(5)
                        mt_line_synt.insert(5, 1)
                        rr = 0
                    for el in next_pred_fieldmass:
                        prevv.fields.append(el)
                    mod_pred = Predicate(prevv.pred, sentind, prevv.fields, mt_line_synt)
                    predicate_collection.pop(-1)
                    predicate_collection.append(mod_pred)
                # Если текущий эл-т просто последни в предл
                elif ind+1 >= len(chunkedsent):
                    mt_line_synt = [0] * 7
                    mt_line_synt.pop(2)
                    mt_line_synt.insert(2, 1)
                    nn = 0
                    if lnn >= 1:
                        mt_line_synt.pop(1)
                        mt_line_synt.insert(1, 1)
                        lnn = 0
                    if fd >= 1:
                        mt_line_synt.pop(3)
                        mt_line_synt.insert(3, 1)
                        fd = 0
                    if rr >= 1:
                        mt_line_synt.pop(5)
                        mt_line_synt.insert(5, 1)
                        rr = 0
                    if cr >= 1:
                        mt_line_synt.pop(0)
                        mt_line_synt.insert(0, 1)
                        cr = 0
                    fic_pred = Predicate('None', sentind, next_pred_fieldmass, mt_line_synt)
                    predicate_collection.append(fic_pred)
                # если подряд два подлежащих, то одному из них делаем мнимый предикат
                elif sequence[nb+1]-ind == 1 and sequence[nb+1] in subjind:
                    mt_line_synt = [0] * 7
                    mt_line_synt.pop(2)
                    mt_line_synt.insert(2, 1)
                    nn = 0
                    if lnn >= 1:
                        mt_line_synt.pop(1)
                        mt_line_synt.insert(1, 1)
                        lnn = 0
                    if fd >= 1:
                        mt_line_synt.pop(3)
                        mt_line_synt.insert(3, 1)
                        fd = 0
                    if rr >= 1:
                        mt_line_synt.pop(5)
                        mt_line_synt.insert(5, 1)
                        rr = 0
                    fic_pred = Predicate('None', sentind, next_pred_fieldmass, mt_line_synt)
                    predicate_collection.append(fic_pred)
                    next_pred_fieldmass = []

            # СКАЗУЕМОЕ
            elif ind in predind:
                pred_fields = []
                mt_line_synt = [0] * 7
                if nn >= 1:
                    mt_line_synt.pop(2)
                    mt_line_synt.insert(2, 1)
                    nn = 0
                # Передаем левое поле из предыдущего разбора
                if ln >= 1:
                    mt_line_synt.pop(1)
                    mt_line_synt.insert(1, 1)
                    ln = 0
                # И поле с союзом
                if cr >= 1:
                    mt_line_synt.pop(0)
                    mt_line_synt.insert(0, 1)
                    cr = 0
                if lnn >= 1:
                    mt_line_synt.pop(1)
                    mt_line_synt.insert(1, 1)
                    lnn = 0
                if fd >= 1:
                    mt_line_synt.pop(3)
                    mt_line_synt.insert(3, 1)
                    fd = 0
                if rr >= 1:
                    mt_line_synt.pop(5)
                    mt_line_synt.insert(5, 1)
                    rr = 0
                # Добавляем в массив все предыдущие поля (если есть)
                if next_pred_fieldmass:
                    for elem in next_pred_fieldmass:
                        pred_fields.append(elem)
                next_pred_fieldmass.clear()
                # Если в списке эл-т первый, но в предложении перед ним что-то есть
                if ind > 0 and nb == 0:
                    fieldsmass.append(LNField(chunkedsent[:ind]))
                    pred_fields.append(LNField(chunkedsent[:ind]))
                    mt_line_synt.pop(1)
                    mt_line_synt.insert(1, 1)
                sub.append(chunkedsent[ind])
                fvs = FVField(sub)
                fieldsmass.append(fvs)
                pred_fields.append(fvs)
                mt_line_synt.pop(4)
                mt_line_synt.insert(4, 1)
                # Если между текущим эл-том и следующим есть поля
                if nb+1 < len(sequence) and sequence[nb+1]-ind > 1:
                    # следующий эл-т - подлежащее, а текущее сказуемое первое в списке
                    if sequence[nb+1] in subjind and nb == 0:
                        fieldsmass[-1].pair = chunkedsent[sequence[nb+1]]
                        fieldsmass.append(FDField(chunkedsent[ind + 1:sequence[nb+1]]))
                        pred_fields.append(FDField(chunkedsent[ind + 1:sequence[nb+1]]))
                        mt_line_synt.pop(3)
                        mt_line_synt.insert(3, 1)
                    # Следующий эл-т - подлежащее, а текущее сказ в списке не первое
                    elif sequence[nb+1] in subjind and nb != 0:
                        fieldsmass[-1].pair = chunkedsent[sequence[nb + 1]]
                        fieldsmass.append(RRField(chunkedsent[ind + 1:sequence[nb+1]]))
                        pred_fields.append(RRField(chunkedsent[ind + 1:sequence[nb+1]]))
                        mt_line_synt.pop(5)
                        mt_line_synt.insert(5, 1)
                    # Следующий эл-т - сказуемое или союз
                    elif sequence[nb+1] in predind or sequence[nb+1] in crdind:
                        fieldsmass.append(RRField(chunkedsent[ind + 1:sequence[nb + 1]]))
                        pred_fields.append(RRField(chunkedsent[ind + 1:sequence[nb + 1]]))
                        mt_line_synt.pop(5)
                        mt_line_synt.insert(5, 1)
                    # Другие случаи
                    else:
                        fieldsmass.append(LNField(chunkedsent[ind + 1:sequence[nb + 1]]))
                        ln += 1
                        next_pred_fieldmass.append(LNField(chunkedsent[ind + 1:sequence[nb + 1]]))
                # если текущий эл-т последний в списке, а в предложении после него еще что-то есть
                elif nb+1 >= len(sequence) and ind+1 < len(chunkedsent):
                    fieldsmass.append(RRField(chunkedsent[ind+1:]))
                    pred_fields.append(RRField(chunkedsent[ind+1:]))
                    mt_line_synt.pop(5)
                    mt_line_synt.insert(5, 1)
                fields_matrix_synt.append(mt_line_synt)
                fieldsmass[fieldsmass.index(fvs)].mtrx_of_flds = mt_line_synt
                gmt = Predicate(fvs, sentind, pred_fields, mt_line_synt)
                predicate_collection.append(gmt)
            # СОЮЗ
            elif ind in crdind:
                cr += 1
                # Союз превый в списке, но в предложении перед ним что-то есть
                if ind > 0 and nb == 0:
                    fieldsmass.append(LNField(chunkedsent[:ind]))
                    next_pred_fieldmass.append(LNField(chunkedsent[:ind]))
                sub.append(chunkedsent[ind])
                fieldsmass.append(CField(sub))
                next_pred_fieldmass.append(CField(sub))
                # если между текущим эл-том и следующим в списке в предложении что-то есть
                if nb+1 < len(sequence) and sequence[nb+1]-ind > 1:
                    fieldsmass.append(LNField(chunkedsent[ind + 1:sequence[nb+1]]))
                    next_pred_fieldmass.append(LNField(chunkedsent[ind + 1:sequence[nb+1]]))
                    lnn += 1
                # если союз последний в списке, но не в предложении
                elif nb+1 >= len(sequence) and ind+1 < len(chunkedsent):
                    fieldsmass.append(RRField(chunkedsent[ind+1:]))
    else:
        fieldsmass.append(UKField(chunkedsent))
        mt = []
        mt.append(UKField(chunkedsent))
        fc_pred = Predicate('None', sentind, mt, [0, 0, 0, 0, 0, 0, 1])
        predicate_collection.append(fc_pred)

    return predicate_collection

# Возвращает топологические поля для всего текста
def allfields(chsentence):
    af = []
    for n, chunk in enumerate(chsentence):
        for pred in gettopfield(chunk, n):
            af.append(pred)
    return af

if __name__ == '__main__':
    allfields(btset2)