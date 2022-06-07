# -*- coding: utf-8 -*-
"""
Created on Thu May 12 11:34:38 2022
@author: Nicola
"""

from flask import Flask, request, render_template, url_for, session, redirect, abort
from flask.json import jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
import secrets
from functools import wraps
from database import DB
from analizzatore import Sentiment, Feel
from generatore_credenziali import Generatore_credenziali

#creazione webapp
app = Flask(__name__)
app.config.from_mapping(SECRET_KEY=secrets.token_hex())
app.url_map.strict_slashes = False #cosi' url funziona sia /xyz che /xyz/
#creazione servizio invio email
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = "***"
app.config["MAIL_PASSWORD"] = "***"
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
mail = Mail(app)
#connessione db
db = DB()
db.connetti_db()
#dichiarazione sentiment/feel analisys
sentiment = Sentiment()
feel = Feel()
#generatore di credenziali per utenti che si registrano
credenziali = Generatore_credenziali()


#wrapper/decorator per impedire di accedere a url dell'app senza prima essersi loggati
def richiesto_login(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "idutente" in session:
            return f(*args, **kwargs)
        else:
            return render_template("index.html")
    return wrap


@app.route("/")
def index():
    #se l'utente è loggato allora non può ritornare alla pagina di login
    if "idutente" in session:
        return render_template("home.html")
    else:
        return render_template("index.html")


@app.route("/home", methods=["POST"])
def gestione_login():
    username_inserito = request.form["username"]
    password_inserita = request.form["password"]
    #si controlla l'username: se esiste si ritorna un dizionario con l'idutente e la password
    res = db.controlla_login(username_inserito)
    if res:
        #controllo password
        vera_password = res["psw"] #la password hash nel database
        if check_password_hash(vera_password, password_inserita):
            session["idutente"] = res["id_utente"]
            return render_template("home.html")
        else:
            #errore password
            return render_template("index.html", mex_errore="Errore! Password inserita non corretta.")
    else:
        #errore username/attivazione
        return render_template("index.html", mex_errore="Errore! Username inserito non corretto. Assicurarsi di aver attivato l'account.")


@app.route("/registrazione")
def registrazione():
    #se l'utente è loggato allora non può ritornare alla pagina di registrazione
    if "idutente" in session:
        return render_template("home.html")
    else:
        return render_template("registrazione.html")
    


@app.route("/", methods=["POST"])
def registra_utente():
    nome_utente = request.form["nome"]
    cognome_utente = request.form["cognome"]
    email_utente = request.form["mail"]
    #generazione username+password
    username = credenziali.genera_username(nome_utente, cognome_utente)
    password = credenziali.genera_password()
    password_hash = generate_password_hash(password) #password salata per il db
    #inserimento nel db del nuovo utente MA ANCORA NON ATTIVATO
    db.registra_utente(nome_utente, cognome_utente, email_utente, username, password_hash)
    id_nuovo_utente = db.id_ultimo_utente_registrato()["id_utente"]
    #mail
    msg = Message("Attivazione account per mood della Darsena", sender="nicola110400@gmail.com", recipients=[email_utente])
    msg.html = ('<p>NON RISPONDERE A QUESTA E-MAIL</p>'
                '<p>Ecco qui sotto le credenziali con le quali potrai accedere.</p>'
                '<p>Username: ' + username + '</p>'
                '<p>Password:' + password + '</p>'
                '<p>Cliccando su <a href="' + request.host_url + url_for('attivazione_credenziali', idutente=id_nuovo_utente) + '" target="_blank">questo link</a> il tuo account verrà attivato.</p>')
    mail.send(msg)
    return render_template("index.html")


@app.route("/attivazione-credenziali-utente-<int:idutente>")
def attivazione_credenziali(idutente):
    if not db.utente_gia_attivato(idutente):
        #attivazione
        db.attivazione_utente(idutente)
        return render_template("index.html")
    else:
        #utente è già attivato
        abort(404)


@app.route("/logout-utente")
@richiesto_login
def logout_utente():
    print("pre eliminazione:", session)
    session.pop("idutente", None)
    print("eliminazione:", session)
    return redirect(url_for("index"))


@app.route("/home")
@richiesto_login
def home():
    return render_template("home.html")


@app.route("/home/dashboard-darsena")
@richiesto_login
def visualizza_mood():
    #preparazione piechart
    testi_x_sentiment = db.totale_sentiment_testi_darsena()
    nneg, npos, nneu = estrapola_numero_sentiment(testi_x_sentiment)
    n_sentiment = {'positivi': npos, 'negativi': nneg, 'neutrali': nneu}
    #preparazione linechart
    dati_linechart = db.date_sentiment_darsena()
    date_line, npos_line, nneg_line, nneu_line = spacchetta_numero_sentiment_date(dati_linechart)
    date_n_sentiment = {'date': date_line, 'positivi': npos_line, 'negativi': nneg_line, 'neutrali': nneu_line}
    return render_template("grafici.html", lista_valori_pie=n_sentiment, lista_valori_line=date_n_sentiment)


@app.route("/home/dashboard-darsena/analizza-testo")
@richiesto_login
def analizza_testo():
    return render_template("analizza.html")


@app.route("/home/dashboard-darsena/analizza-testo", methods=["POST"])
@richiesto_login
def gestione_analisi():
    azione = request.form["azione"]
    
    if azione == "Analizza testo":
        modalita = request.form["modalita"]
        if modalita == "file":
            file_testo = request.files["testo"]
            testo = file_testo.read().decode("utf-8")
        else:
            testo = request.form["testo"]
         
        label_sent, score_sent = sentiment.ottieni_sentiment(testo)
        score_sent = round(score_sent * 100, 1)
        label_feel = feel.ottieni_feel(testo)
        return jsonify({'testo': testo, 'etichetta_sentiment': label_sent, 'punteggio_sentiment': score_sent, 'etichetta_feel': label_feel})
    else:
        contenuto = request.form["testo"]
        sentiment_ottenuto = request.form["sentiment"]
        punteggio_ottenuto = float(request.form["punteggio"])
        feel_ottenuto = request.form["feel"]
        origine = request.form["origine"]
        utente = session["idutente"]
        #inserimento nel db
        res = db.inserisci_testo(contenuto, sentiment_ottenuto, punteggio_ottenuto, feel_ottenuto, origine, utente)
        return jsonify({'risposta': res})


@app.route("/home/dashboard-darsena/visualizza-testi")
@richiesto_login
def visualizza_testi():
    db.elimina_filtro_testi_darsena()
    testi_x_sentiment = db.totale_sentiment_testi_darsena()
    tot_ris = db.totale_testi_darsena()["totale"]
    risultato = db.preleva_testi_darsena()
    nneg, npos, nneu = estrapola_numero_sentiment(testi_x_sentiment)
    return render_template("dati.html", dati=risultato, totale=tot_ris, testi_pos=npos, testi_neg=nneg, testi_neu=nneu)


@app.route("/home/dashboard-darsena/visualizza-testi", methods=["POST"])
@richiesto_login
def gestione_testi():
    azione = request.form["azione"]
    scelta = request.form["scelta"]
    if azione == "filtro":
        #se si seleziona un filtro si crea una vista col db e si ritornano i risultati della query eseguita su di essa
        db.elimina_filtro_testi_darsena()
        risultato = db.preleva_testi_darsena() if scelta == "nessuno" else db.filtra_testi_darsena(scelta)
    else:
        risultato = db.ordina_testi(scelta)
    return jsonify({'dati': risultato})


@app.route("/home/dashboard-darsena/visualizza-testi/testo-<int:idtesto>")
@richiesto_login
def visualizza_dettaglio_testo(idtesto):
    risultato = db.dettaglio_testo(idtesto)
    return render_template("testo.html", dato=risultato)


@app.route("/home/dashboard-darsena/visualizza-testi/elimina", methods=["POST"])
@richiesto_login
def elimina_testo():
    idtesto = int(request.form["idtesto"])
    db.elimina_testo(idtesto)
    return jsonify({'risposta': url_for("visualizza_testi")})


def spacchetta_numero_sentiment_date(lista_dizionario):
    date, npos, nneg, nneu = [], [], [], []
    for dic in lista_dizionario:
        date.append(dic['data_aggiunta'])
        npos.append(dic['tot_pos'])
        nneg.append(dic['tot_neg'])
        nneu.append(dic['tot_neu'])
    return date, npos, nneg, nneu


def estrapola_numero_sentiment(lista_dizionario):
    nneg, npos, nneu = 0, 0, 0
    for elem in lista_dizionario:
        if(elem['sentiment'] == 'negativo'):
            nneg = elem['numero']
        elif(elem['sentiment'] == 'positivo'):
            npos = elem['numero']
        else:
            nneu = elem['numero']
    return nneg, npos, nneu


if __name__ == '__main__':
    app.run()