import copy

from database.meteo_dao import MeteoDao
from model.situazione import Situazione
import datetime


class Model:
    def __init__(self):
        self.sequenza = []
        self.situazioni = MeteoDao.get_all_situazioni()

        # correzione
        self._costo_minimo = -1
        self._sequenza_ottima = []

    def handle_umidita_media(self, mese):
        situazioni = MeteoDao.get_all_situazioni()
        #print(situazioni)
        medie = [] # in ordine genova, milano, torino
        citta3 = ['Genova', 'Milano', 'Torino']
        for citta in citta3:
            lista = []
            for situazione in situazioni:
                #print(situazione.data.month)
                #print("situazione data "+situazione.data.month)
                #print("mese "+mese)
                if citta == situazione.localita and int(mese) == situazione.data.month:
                    lista.append(situazione.umidita)

            media = sum(lista)/len(lista)
            medie.append(round(media, 4))

        return medie

    """
    def calcola_umidita_media(self, mese)
        return MeteoDao.calcola_umidita_media(mese)
    """


    def handle_calcola_sequenza(self, mese):


        self.sequenza_ricorsione([], mese)

    def sequenza_ricorsione(self, parziale, mese):
        # condizione terminale: ritorna sequenza di situazioni ottima quando giorno > 15
        if len(parziale) == 15:
            return

        # primo giorno
        elif len(parziale) == 0:
            minimo = Situazione("", datetime.date(0000, 00, 00), 101) # per fare il confronto
            for situazione in self.situazioni:
                if len(parziale) + 1 == situazione.data.day and mese == situazione.data.month:
                    if situazione.umidita < minimo.umidita:
                        minimo = situazione

            parziale.append(minimo)
            self.sequenza_ricorsione(parziale, mese)

        else:
            ultimaSituazione = parziale[-1]
            minimo = Situazione("", datetime.date(0000, 00, 00), 101)  # per fare il confronto
            for situazione in self.situazioni:
                if len(parziale) + 1 == situazione.data.day and mese == situazione.data.month:
                    if situazione.umidita < minimo.umidita:
                        minimo = situazione

    def calcola_sequenza(self, mese):
        self._costo_minimo = -1
        self._sequenza_ottima = []
        # per prima cosa prendo i primi 15 giorni del mese selezionato per ogni città: faccio query sql
        situazioni_meta_mese = MeteoDao.get_situazioni_meta_mese(mese)
        self._ricorsione([], situazioni_meta_mese)
        return self._sequenza_ottima, self._costo_minimo


    def _ricorsione(self, parziale, situazioni):
        # caso terminale:
        if len(parziale) == 15:
            # calcola costo
            costo = self._calcola_costo(parziale)
            if self._costo_minimo == -1 or costo < self._costo_minimo:
                self._costo_minimo = costo
                self._sequenza_ottima = copy.deepcopy(parziale)


            print(parziale)

        else:
            day = len(parziale) + 1
            for situazione in situazioni[(day-1)*3: day*3]: # *3 intende i blocchi, cicla ogni volta
                # solo sulle 3 situazioni che mi serviranno
                # if situazione.data.day == day: # alternativa

                # qui c'è anche da fare il controllo dei vincoli soddisfatti (funzione apposita)
                if self._vincoli_soddisfatti(parziale, situazione):
                    parziale.append(situazione)
                    self._ricorsione(parziale, situazioni)
                    parziale.pop()

    def _vincoli_soddisfatti(self, parziale, situazione) -> bool: # ritorna un boolean
        # Vincolo 1) check che non sono stato già 6 giorni nella stessa città
        counter = 0
        for fermata in parziale:
            if fermata.localita == situazione.localita:
                counter += 1
        if counter >= 6:
            return False

        # Vincolo 2) check che il tecnico si fermi almeno 3 giorni consecutivi
        # se la sequenza ha 1 o 2 elementi, posso solo rimettere il primo
        if len(parziale) <= 2 and len(parziale) > 0:
            if situazione.localita != parziale[0].localita:
                return False
        # se la mia parziale ha almeno 3 elementi, devo controllare gli ultimi 3 e vedere se il
        # tecnico si è fermato almeno 3 giorni di fila nello stesso posto
        elif len(parziale) > 2:
            sequenza_finale = parziale[-3:] # ultimi 3 elementi della sequenza: parte da -3
            prima_fermata = sequenza_finale[0].localita # primo di questi ultimi 3 giorni
            counter = 0
            for fermata in sequenza_finale:
                if fermata.localita == prima_fermata:
                    counter += 1
            if counter < 3 and situazione.localita != sequenza_finale[-1].localita:
                return False


        # ho soddisfatto tutti i vincoli
        return True

    def _calcola_costo(self, parziale):
        costo = 0
        for i in range(len(parziale)):
            # 1) costo dell'umidità
            costo += parziale[i].umidita
            if i <= 2: # primi 2 giorni
                if parziale[i].localita != parziale[0].localita:
                    costo += 100
            elif i > 2: # altri giorni
                ultime_fermate = parziale[i-2:i+1] # i+1 è escluso
                if (ultime_fermate[2].localita != ultime_fermate[0].localita or
                    ultime_fermate[2].localita != ultime_fermate[1].localita):
                    costo += 100

        return costo
