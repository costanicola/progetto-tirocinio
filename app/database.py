# -*- coding: utf-8 -*-
"""
Created on Sat May 14 20:48:36 2022
@author: Nicola
"""

import mysql.connector
from datetime import datetime

class DB():
    
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    def connetti_db(self):
       self.conn = mysql.connector.connect(user='***', 
                                           password='***', 
                                           host='127.0.0.1',
                                           database='***')
       self.cursor = self.conn.cursor(dictionary=True, buffered=True)
    
    def registra_utente(self, nome, cognome, email, username, password):
        insert = ("INSERT INTO utenti "
                  "(nome, cognome, email, username, psw) "
                  "VALUES (%s, %s, %s, %s, %s)")
        param = (nome, cognome, email, username, password)
        self.cursor.execute(insert, param)
        self.conn.commit()
    
    def id_ultimo_utente_registrato(self):
        query = ("SELECT MAX(id_utente) AS id_utente "
                 "FROM utenti")
        self.cursor.execute(query)
        return self.cursor.fetchone()
    
    def attivazione_utente(self, idutente):
        update = ("UPDATE utenti "
                  "SET attivato = 1 "
                  "WHERE id_utente = %s")
        param = (idutente, )
        self.cursor.execute(update, param)
        self.conn.commit()
        
    def utente_gia_attivato(self, idutente):
        query = ("SELECT attivato "
                 "FROM utenti "
                 "WHERE id_utente = %s")
        param = (idutente, )
        self.cursor.execute(query, param)
        if self.cursor.rowcount >= 1:
            if self.cursor.fetchone()["attivato"] == 1:
                return True
        return False
    
    def controlla_login(self, username):
        query = ("SELECT id_utente, psw "
                 "FROM utenti "
                 "WHERE attivato = 1 AND username = %s")
        param = (username, )
        self.cursor.execute(query, param)
        if self.cursor.rowcount >= 1:
            return self.cursor.fetchone()
        else:
            return {}
    
    def inserisci_testo(self, contenuto, sentiment, punteggio, feel, origine, utente):
        insert = ("INSERT INTO testi "
                  "(contenuto, data_aggiunta, origine, sentiment, punteggio_sentiment, feeling, modificabile, id_utente) "
                  "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")
        param = (contenuto, datetime.today().strftime('%Y-%m-%d'), origine, sentiment, punteggio, feel, 0, utente)
        try:
            self.cursor.execute(insert, param)
            self.conn.commit()
        except mysql.connector.IntegrityError:
            return "Errore dell'inserimento nel database del testo analizzato!"
        return "Analisi salvata con successo!"
    
    def preleva_testi_darsena(self):
        query = ("SELECT id_testo, contenuto, data_aggiunta, sentiment "
                 "FROM testi "
                 "WHERE origine IN ('caricato a mano', 'caricato via file') "
                 "ORDER BY data_aggiunta DESC")
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def totale_testi_darsena(self):
        query = ("SELECT COUNT(*) AS totale "
                 "FROM testi "
                 "WHERE origine IN ('caricato a mano', 'caricato via file')")
        self.cursor.execute(query)
        return self.cursor.fetchone()
    
    def totale_sentiment_testi_darsena(self):
        query = ("SELECT sentiment, COUNT(*) AS numero "
                 "FROM testi "
                 "WHERE origine IN ('caricato a mano', 'caricato via file') "
                 "GROUP BY sentiment")
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def date_sentiment_darsena(self):
        query = ("SELECT data_aggiunta, "
                 "(SELECT COUNT(*) "
                 "FROM testi AS t1 "
                 "WHERE t1.data_aggiunta = t.data_aggiunta AND t1.sentiment = 'positivo' "
                 "AND origine IN ('caricato a mano', 'caricato via file')) AS tot_pos, "
                 "(SELECT COUNT(*) "
                 "FROM testi as t1 "
                 "WHERE t1.data_aggiunta = t.data_aggiunta AND t1.sentiment = 'negativo' "
                 "AND origine IN ('caricato a mano', 'caricato via file')) as tot_neg, "
                 "(SELECT COUNT(*) "
                 "FROM testi as t1 "
                 "WHERE t1.data_aggiunta = t.data_aggiunta AND t1.sentiment = 'neutrale' "
                 "AND origine IN ('caricato a mano', 'caricato via file')) as tot_neu "
                 "FROM testi t "
                 "WHERE origine IN ('caricato a mano', 'caricato via file') "
                 "GROUP BY data_aggiunta "
                 "ORDER BY data_aggiunta")
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def filtra_testi_darsena(self, filtro):
        view = ("CREATE VIEW testi_filtrati (id_testo, contenuto, data_aggiunta, sentiment) AS "
                "SELECT id_testo, contenuto, data_aggiunta, sentiment "
                "FROM testi "
                "WHERE origine IN ('caricato a mano', 'caricato via file') AND sentiment = %s "
                "ORDER BY data_aggiunta DESC")
        param = (filtro, )
        self.cursor.execute(view, param)
        query = ("SELECT id_testo, contenuto, data_aggiunta, sentiment "
                 "FROM testi_filtrati")
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def elimina_filtro_testi_darsena(self):
        drop = ("DROP VIEW IF EXISTS testi_filtrati")
        self.cursor.execute(drop)
    
    def ordina_testi(self, ordine):
        show = ("SHOW TABLES IN db_testi_valutati LIKE 'testi_filtrati'")
        self.cursor.execute(show)
        if self.cursor.rowcount >= 1:
            #se esiste la vista (testi filtrati) allora si ordina quella
            query = ("SELECT id_testo, contenuto, data_aggiunta, sentiment "
                     "FROM testi_filtrati "
                     "ORDER BY data_aggiunta " + ordine)
        else:
            #altrimenti vuol dire che non si è filtrata e si ordina l'originale
            query = ("SELECT id_testo, contenuto, data_aggiunta, sentiment "
                     "FROM testi "
                     "WHERE origine IN ('caricato a mano', 'caricato via file') "
                     "ORDER BY data_aggiunta " + ordine)
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def dettaglio_testo(self, idtesto):
        query = ("SELECT id_testo, contenuto, data_aggiunta, origine, sentiment, punteggio_sentiment, feeling, nome, cognome, email "
                 "FROM testi t JOIN utenti u ON (t.id_utente = u.id_utente) "
                 "WHERE id_testo = %s")
        param = (idtesto, )
        self.cursor.execute(query, param)
        return self.cursor.fetchone()

    def elimina_testo(self, idtesto):
        delete = ("DELETE FROM testi "
                  "WHERE id_testo = %s")
        param = (idtesto, )
        self.cursor.execute(delete, param)
        self.conn.commit()
    
    
    