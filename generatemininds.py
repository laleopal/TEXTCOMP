from decimal import Decimal

def generatenumbers(m): #[[1, 2, 5], [3, 6, 7], [4, 8, 9, 10]]
    indmass=[]
    sumlen=0
    for f in range(len(m)):
        indmass.append(0) #заполняем массив нулями по количеству подмножеств в исходном множестве
        sumlen+=len(m[f]) #считаем общее к-во элементов в этих подмножествах
    for g in range(sumlen): #выполняем цикл столько раз, сколько элементов всего в подмножествах
        ytf=[]
        for i, nb in enumerate(m):
            if indmass[i]<len(nb): #если в данном подмножестве есть нерассмотренные элементы, добавляем первый из них в массив для сравнения
                ytf.append(nb[indmass[i]])
            else:
                ytf.append(Decimal('Infinity')) #если эл-ты подмножества закончились, добавляем бесконечность
        yield min(ytf) #выдаем меньшее число из массива
        indmass[ytf.index(min(ytf))]+=1 #сдвигаемся на один элемент вправо в исходном подмножестве, где встретился наименьший элемент

if __name__ == '__main__':
    generatenumbers([[1, 2, 5], [3, 6, 7], [4, 8, 9, 10]])
