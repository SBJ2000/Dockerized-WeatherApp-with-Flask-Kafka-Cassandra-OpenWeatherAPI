# Dockerized-WeatherApp-with-Flask-Kafka-Cassandra-OpenWeatherAPI
![Project Logo](https://github.com/SBJ2000/Dockerized-WeatherApp-with-Flask-Kafka-Cassandra-OpenWeatherAPI/blob/main/Images/Logo.png)

## Project Description
The goal of the project is to create a Weather web application (Getting the weather information from the Open Weather API) using Docker and modern technologies such as: Python for the management of the back end side and with its Flask library for the Front end, Kafka to control the flow of data between the database data and the application and cassandra for data storage.
The application contains advanced features like email notifications, history, recommendation system and feed management using Kafka.
All these technologies are included in a development environment based on Docker containers to facilitate implementation.
The work is also devided into sprint and adapt the scrum methodologie.

### Project Architecture :
Before going into the application, we need to understand correctly the architecture that the developer adapted to build his project & what are the toold needed, which is in this case:
![Architecture](https://github.com/SBJ2000/Dockerized-WeatherApp-with-Flask-Kafka-Cassandra-OpenWeatherAPI/blob/main/Images/Architecture.png)

### Users & roles :
The application is designed for 2 types of users , and each of them has a specific privileges:
![Users](https://github.com/SBJ2000/Dockerized-WeatherApp-with-Flask-Kafka-Cassandra-OpenWeatherAPI/blob/main/Images/Users.png)

## Installation & Usage

### Prerequisites:
![Python](https://img.shields.io/badge/Language-Python-blue)

    Python: Proficiency in Python programming language, including knowledge of data types, functions, modules, and libraries.
![Flask](https://img.shields.io/badge/Framework-Flask-blue)

    Flask: Understanding of Flask framework concepts, such as routing, templates, forms, and RESTful API development.

![Docker](https://img.shields.io/badge/Tool-Docker-blue)

    Docker: Knowledge of Docker concepts, including containerization, Dockerfile, Docker Compose, and container orchestration.

![Kafka](https://img.shields.io/badge/Tool-Kafka-red)

    Kafka: Understanding of Kafka messaging system, including topics, producers, consumers, and message processing.

![Cassandra](https://img.shields.io/badge/Database-Cassandra-blue)

    Cassandra: Familiarity with Cassandra NoSQL database, including data modeling, querying, and configuration.

![API](https://img.shields.io/badge/API-Development-green)

    API Integration: Experience in integrating external APIs, specifically the Open Weather API, and handling data retrieval and processing.


![Visual Studio Code](https://img.shields.io/badge/IDE-Visual%20Studio%20Code-blue)

    Integrated Development Environment (IDE): Choose an IDE of your preference for Python and Flask development, such as Visual Studio Code.

### Installation:
After installing Docker on your machine and having the project you need to redirect to the folder that contain the docker compose to build the Docker images for your application using the docker-compose command:

docker-compose build

Once the images are built, you can start the Docker containers using the following command:

docker-compose up
This command will start all the services defined in your docker-compose.yml file.

Access your web application by opening a web browser and entering the appropriate URL (Note that you acces acces the URL from the docker desktop if you simply click on the url of the container)

It's important to have this librairies included in your requirement file (you do not have to install them using pip locally beacause you are working with Docker):
![Libs](https://github.com/SBJ2000/Dockerized-WeatherApp-with-Flask-Kafka-Cassandra-OpenWeatherAPI/blob/main/Images/libs.png)
