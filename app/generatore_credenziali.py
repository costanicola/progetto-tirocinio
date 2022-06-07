# -*- coding: utf-8 -*-
"""
Created on Thu May 19 16:10:34 2022
@author: Nicola
"""

import string
import secrets

class Generatore_credenziali():
    
    def __init__(self):
        #alfabeto di lettere e numeri da cui generare la password
        self.alfabeto = string.ascii_letters + string.digits
        
    def genera_username(self, nome, cognome):
        """
        Genera un username dati un nome e un cognome.
        Ritorna una stringa formata dalla concatenazione del nome 
        e cognome con un punto e un numero casuale tra 0 e 9 finale.
        Es. nicola.costa1 oppure mario.rossi7
        """
        return nome.lower() + "." + cognome.lower() + str(secrets.randbelow(10))
    
    def genera_password(self):
        """
        Genera una password di 10 caratteri con almeno una 
        lettera minuscola, una lettera maiuscola e un numero.
        """
        while True:
            password = ''.join(secrets.choice(self.alfabeto) for i in range(10))
            if (any(c.islower() for c in password) and
                any(c.isupper() for c in password) and
                any(c.isdigit() for c in password)):
                break
        return password