# Médiathèque Villejuif 

Récupérer la liste des emprunts sur des comptes à la Médiathèque de Villejuif,
avec Selenium et Python.

## Installation

    python -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install selenium pandas

## Configuration

Un fichier de configuration, appelé `config.ini` doit être rempli, avec les
login et mot de passe utilisés sur le site. Voici un exemple :

````
[Serena Williams]
username: 0011111
password: XXXXXXX

[Lorraine Hipsaume]
username: 0022222
password: YYYYYYY
````

## TODO

- Fusionner les dictionnaires de prêts des utilisateurs pour une sortie commune
- Permettre le tri (par date ou par lieu) des sorties
