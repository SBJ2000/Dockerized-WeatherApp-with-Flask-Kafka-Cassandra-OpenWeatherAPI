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

api_key = '5fefa376e3593b40bebd1cef59efbf95'


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
# Define a model to represent the users table in Cassandra
class users(Model):
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    nom = columns.Text()
    email = columns.Text(primary_key=True)
    password = columns.Text()
    fav_cities = columns.List(columns.Text)

def send_email():
    # Connect to the Cassandra cluster
    connection.setup(['cassandra'], "weather_data_keyspace", port=9042)

    # Get all the users from the Cassandra database
    all_users = users.objects()

    # Informations d'identification pour le serveur SMTP
    smtp_server = 'smtp.gmail.com'
    port = 587
    username = '2ingidl1isi@gmail.com'
    password = 'rihnpblutdndxvof'

    # Loop through all the users and send them an email
    for user in all_users:
        # Get the weather data for each of the user's favorite cities
        city_weather_data = []
        for city in user.fav_cities:
            weather_data = get_weather_data(city)
            if weather_data is not None:
                city_weather_data.append(weather_data)

        # Create the email message
        msg = EmailMessage()
        msg['Subject'] = 'Alert Meteo'
        msg['From'] = '2ingidl1isi@gmail.com'
        msg['To'] = user.email

        # Add the weather data to the email body
        if len(city_weather_data) > 0:
            email_body = 'Here are the weather forecasts for your favorite cities:\n\n'
            for data in city_weather_data:
                email_body += f"{data['city']}:\n\n weather: {data['weather']}, temperature: {data['temp']}°C, humidity: {data['humidity']}%, pressure: {data['pressure']} hPa, precipitation: {data['precipitation']} mm\n\n"
                # Check for extreme weather conditions and add recommendations
                if data['temp'] > 35:
                    email_body += f"It's extremely hot in {data['city']}! Remember to drink plenty of water and protect yourself from the sun.\n"
                elif data['temp'] < 0:
                    email_body += f"It's very cold in {data['city']}! Make sure to dress warmly and take precautions to avoid frostbite.\n"
                if data['humidity'] > 80:
                    email_body += f"The air is very humid in {data['city']}. Make sure to protect yourself against humidity to avoid any risk of illness.\n"
                if data['pressure'] < 970:
                    email_body += f"The atmospheric pressure is very low in {data['city']}. Be prepared to face unstable weather conditions.\n"
                if data['precipitation'] > 10:
                    email_body += f"It's raining heavily in {data['city']}. Be prepared to face difficult weather conditions on the road.\n"
            msg.set_content(email_body)
        else:
            msg.set_content('No weather data available for your favorite cities.') 


        # Send the message using the SMTP server
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)

# Planification de l'envoi de l'e-mail toutes les deux heures à partir de 8h du matin
schedule.every().day.at("08:00").do(send_email)
schedule.every().day.at("10:00").do(send_email)
schedule.every().day.at("12:00").do(send_email)
schedule.every().day.at("14:00").do(send_email)
schedule.every().day.at("16:00").do(send_email)
schedule.every().day.at("18:00").do(send_email)
schedule.every().day.at("20:00").do(send_email)
schedule.every().day.at("00:37").do(send_email)

while True:
    # Exécution des tâches planifiées
    schedule.run_pending()
    time.sleep(1)