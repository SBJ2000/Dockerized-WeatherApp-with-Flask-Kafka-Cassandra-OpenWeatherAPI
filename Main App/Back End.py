import requests
from flask import Flask, render_template, request ,redirect, url_for
from cassandra.cluster import Cluster
from kafka import KafkaProducer, KafkaConsumer
import json
from cqlengine import columns
from cqlengine.models import Model
from cqlengine import connection
from uuid import uuid1
from datetime import datetime,date,timedelta
import uuid
from cassandra.cqlengine.query import DoesNotExist
import smtplib
from email.message import EmailMessage
import schedule
import time
import subprocess

# Initialisation de l'application Flask
app = Flask(__name__)

# Initialisation des paramètres pour Kafka
bootstrap_servers = ['kafka:9092']
topic = 'weather_data'

# Initialisation du producteur Kafka
producer = KafkaProducer(bootstrap_servers=bootstrap_servers)

# Initialisation du consommateur Kafka
consumer = KafkaConsumer(topic, bootstrap_servers=bootstrap_servers)

api_key = ''

def get_weather_data(city):
    weather_data = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&APPID={api_key}")

    if weather_data.json()['cod'] == '404':
        return None
    else:
        weather = weather_data.json()['weather'][0]['main']
        temp = round(weather_data.json()['main']['temp'])
        humidity = weather_data.json()['main']['humidity']
        pressure = weather_data.json()['main']['pressure']
        if 'rain' in weather_data.json():
            precipitation = weather_data.json()['rain'].get('1h', 0)
        elif 'snow' in weather_data.json():
            precipitation = weather_data.json()['snow'].get('1h', 0)
        else:
            precipitation = 0
        return {'city': city,'weather': weather, 'temp': temp, 'humidity': humidity, 'pressure': pressure, 'precipitation': precipitation}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/logout")
def indexlogout():
    return render_template("index.html")

@app.route("/favorites")
def favorites():
    iduser = request.args.get('iduser')
    email = request.args.get('email')
    
    # Retrieve user's favorite cities
    user = users.objects.filter(id=iduser, email=email).allow_filtering().first()
    fav_cities = user.fav_cities if user else []

    # Retrieve user's name
    nomuser = user.nom if user else ''
    
    # Get weather data for each favorite city
    city_data = []
    for city in fav_cities:
        weather_data = get_weather_data(city)
        if weather_data:
            city_data.append(weather_data)

    return render_template("favorites.html", nomuser=nomuser, iduser=iduser, email=email, city_data=city_data)

@app.route("/history")
def history():
    iduser = request.args.get('iduser')
    email = request.args.get('email')

    # Retrieve user's name
    user = users.objects.filter(id=iduser, email=email).allow_filtering().first()

    # Get weather data for the given user id
    city_data = []
    weather_data_new = WeatherData.objects.filter(user_id=iduser).allow_filtering()
    for data in weather_data_new:
        city_data.append({
            'city': data.city,
            'date': data.event_date,
            'time': data.event_time,
            'temperature': data.temp,
            'humidity': data.humidity,
            'pressure': data.pressure,
            'precipitation': data.precipitation,
            'weather': data.weather
        })
        # Initialize a dictionary to store data for each city
        city_dict = {}

        # Group data by city
        for data in city_data:
            city = data['city']
            if city not in city_dict:
                city_dict[city] = []
            city_dict[city].append(data)

        # Render template with grouped data
    return render_template("history.html", nomuser=user.nom, iduser=iduser, email=email, city_dict=city_dict)

@app.route("/delete_city")
def delete_city():
    iduser = request.args.get('iduser')
    email = request.args.get('email')
    city_to_delete = request.args.get('city')
    app.logger.info(city_to_delete)
    # Retrieve user's favorite cities
    user = users.objects.filter(id=iduser, email=email).allow_filtering().first()
    fav_cities = user.fav_cities if user else []

    # Remove city from favorite cities list
    if city_to_delete in fav_cities:
        fav_cities.remove(city_to_delete)
        user.fav_cities = fav_cities
        user.save()

    # Redirect to favorites page
    return redirect(url_for('favorites', iduser=iduser, email=email))


@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/signin")
def signin():
    return render_template("signin.html")

# Fonction pour envoyer les données météorologiques à Kafka
def send_weather_data(weather_data):
    app.logger.info("success:  les données météorologiques pour la ville spécifiée sont arrivés au producteur")
    app.logger.info("JSON envoyé: %s",json.dumps(weather_data).encode("UTF8"))
    # Envoi des données à Kafka
    producer.send(topic,value=json.dumps(weather_data).encode("UTF8"))
    app.logger.info("success:  les données météorologiques pour la ville spécifiée sont sorties du producteur %s",topic)



# Define a model to represent the users table in Cassandra
class users(Model):
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    nom = columns.Text()
    email = columns.Text(primary_key=True)
    password = columns.Text()
    fav_cities = columns.List(columns.Text)

# Store users data in Cassandra using cqlengine
def Store_SignUp_Info(Name,Email,Password):
    User = users.create(
        nom=Name,
        email=Email,
        password=Password
    )

# Fonction pour récupérer les données météorologiques de Kafka et les stocker dans Cassandra
def consume_weather_data():
    for message in consumer:
        # Récupération des données météorologiques depuis Kafka
        weather_data = message.value.decode()
        # Conversion des données en dictionnaire
        weather_data = json.loads(weather_data)
        # Stockage des données dans Cassandra
        store_weather_data(weather_data)

# Define a model to represent the weather_data table in Cassandra
class WeatherData(Model):
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    city = columns.Text(index=True)
    event_date = columns.Text()
    event_time = columns.Text()
    weather = columns.Text()
    temp = columns.Integer()
    humidity = columns.Integer()
    pressure = columns.Integer()
    precipitation = columns.Float()
    user_id=columns.UUID()

# Connect to the Cassandra cluster
connection.setup(['cassandra'], "weather_data_keyspace", port=9042)

def delete_old_weather_data():
    # get the current date as a datetime.date object
    now_date = datetime.now().date()
    # set the time delta to 16 days
    delta = timedelta(days=16)
    # get the date 16 days ago
    date_limit = now_date - delta

    # delete all weather data with a date before date_limit
    for data in WeatherData.objects():
        event_date = datetime.strptime(data.event_date, '%Y-%m-%d').date()
        if event_date < date_limit:
            data.delete()


# Store weather data in Cassandra using cqlengine
def store_weather_data(weather_data):
    # call the function to delete old weather data
    delete_old_weather_data()
    # get the current date as a datetime.date object
    now_date = datetime.now().date()
    # convert the date to a string
    date_str = now_date.strftime('%Y-%m-%d')
    # get the current time as a datetime object
    now = datetime.now()
    # convert the time to a string
    time_str = now.strftime("%H:%M:%S") # format for hours, minutes, seconds

    weather = WeatherData.create(
        city=weather_data['city'],
        weather=weather_data['weather'],
        temp=weather_data['temp'],
        humidity=weather_data['humidity'],
        pressure=weather_data['pressure'],
        precipitation=weather_data['precipitation'],
        event_date=date_str,
        event_time=time_str,
        user_id=weather_data['iduser']
    )

# Fonction pour vérifier les informations de connexion de l'utilisateur
def SignIn_Info(email, password):
    user = users.objects.filter(email=email, password=password).allow_filtering().first()
    return user
# Fonction pour vérifier les informations de connexion de l'utilisateur
def SignIn_Info_Home(email):
    user = users.objects.filter(email=email).allow_filtering().first()
    return user
# Fonction pour récupérer les données du formulaire signin et enter au compte
@app.route("/signinsucces", methods=['POST'])
def signinsucces():
    if 'Email' in request.form:
        email = request.form['Email']
    if 'Password' in request.form:
        password = request.form['Password']
    user = SignIn_Info(email, password)
    if user:
        return render_template('indexidentifie.html', nom=user.nom, email=user.email, password=user.password,fav_cities=user.fav_cities,iduser=user.id)
    else:
        return render_template('index.html')
# Fonction Home
@app.route("/Home")
def Home():
    email = request.args.get('email')
    user = SignIn_Info_Home(email)
    return render_template('indexidentifie.html', nom=user.nom, email=user.email, password=user.password,fav_cities=user.fav_cities,iduser=user.id)
# Fonction pour récupérer les données du formulaire signup et les stocker dans la base
@app.route("/signupsucces", methods=['POST'])
def signupsucces():
    if 'Name' in request.form:
        Name = request.form['Name']
    if 'Email' in request.form:
        Email = request.form['Email']
    if 'Password' in request.form:
        Password = request.form['Password']
    Store_SignUp_Info(Name,Email,Password)
    return render_template('index.html')

# Fonction pour récupérer les données météorologiques et les stocker dans Kafka
@app.route("/weather", methods=['POST'])
def weather():
    if 'city' in request.form:
        city = request.form['city']
    if 'city_button' in request.form:
        city = request.form['city_button']
    if 'cityname' in request.form:
        city = request.form['cityname']
    weather_data = get_weather_data(city)
    return render_template('weather.html', weather_data=weather_data, city=city)

# Fonction pour récupérer les données météorologiques et les stocker dans Kafka
@app.route("/weatheridentifie", methods=['POST'])
def weatheridentifie():
    if 'city' in request.form:
        city = request.form['city']
    if 'city_button' in request.form:
        city = request.form['city_button']
    if 'cityname' in request.form:
        city = request.form['cityname']
    if 'nomuser' in request.form:
        nomuser = request.form['nomuser']
    if 'fav_cities' in request.form:
        fav_cities = request.form['fav_cities']
    if 'iduser' in request.form:
        iduser = request.form['iduser']
    if 'email' in request.form:
        email = request.form['email']
    weather_data = get_weather_data(city)
    weather_data['iduser'] = iduser
    if weather_data:
        # Envoi des données météorologiques à Kafka
        app.logger.info("success:  récupération des données météorologiques pour la ville spécifiée")
        send_weather_data(weather_data)
    else:
        app.logger.info("Erreur: Impossible de récupérer les données météorologiques pour la ville spécifiée")
    return render_template('weatheridentifie.html', weather_data=weather_data, city=city,nomuser=nomuser,fav_cities=fav_cities,iduser=iduser,email=email)

# Fonction pour récupérer les villes favorites et les stocker dans cassandra
@app.route("/addedfavorite", methods=['POST'])
def addtofav():
    if 'city' in request.form:
        city = request.form['city']
    if 'email' in request.form:
        email = request.form['email']
    if 'iduser' in request.form:
        iduser = request.form['iduser']
     # Add city to user's favorites
    user = users.objects.filter(id=iduser,email=email).allow_filtering().first()
    user.fav_cities.append(city)
    user.save()
    # Redirect user to a new page
    return render_template('indexidentifie.html', nom=user.nom, email=user.email,fav_cities=user.fav_cities,iduser=user.id)

if __name__ == '__main__':

    # Lancement du consommateur Kafka en arrière-plan
    import threading
    t = threading.Thread(target=consume_weather_data)
    t.daemon = True
    t.start()
    subprocess.Popen(["python", "email_sender.py"])
    # Lancement de l'application Flask
    app.run(debug=True, host="0.0.0.0")
