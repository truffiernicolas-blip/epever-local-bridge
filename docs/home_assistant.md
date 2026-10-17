# Installation Home Assistant

## Prérequis

- Home Assistant avec accès au dossier de configuration et aux intégrations personnalisées.
- Clé RJ45 D accessible depuis le serveur sur TCP 8899.
- Identifiant de communication de l'onduleur ; 10 par défaut pour UP HI.
- Fichier privé native_init.bin associé à la passerelle.
- Sauvegarde de la configuration Home Assistant avant installation de code personnalisé.

La plateforme de référence est Home Assistant OS avec Core 2026.10.1 sur Raspberry
Pi 5. Aucun broker MQTT, compte EPEVER cloud ni service permanent sur PC n'est requis.

## Préparation de la session

Cette version importe une initialisation native depuis un fichier PCAP compatible.
La génération universelle à partir du seul numéro de série n'est pas implémentée.
Le fichier est spécifique à la passerelle et doit rester privé.

Pour fournir une session locale compatible, enregistrer une courte connexion
Solar Guardian en mode local, avec un outil Android tel que PCAPdroid filtré sur
l'application. Démarrer l'enregistrement avant la connexion, afficher les mesures
pendant 30 à 60 secondes, puis arrêter. Ne pas activer de déchiffrement TLS et
ne pas actionner les commandes de pilotage.

Sur un PC disposant de Python 3.10 ou supérieur :

```sh
python -m pip install -r requirements-capture.txt
python tools/prepare_ha.py chemin/session.pcap
```

Le programme crée custom_components/epever_local/native_init.bin sans afficher
la négociation. Il refuse d'écraser un fichier existant. L'option --output permet
de choisir un autre emplacement. Les captures dépourvues d'initialisation ou
présentant plusieurs initialisations distinctes sont refusées.

## Copie et activation

Copier le dossier epever_local dans custom_components du répertoire de
configuration Home Assistant. Le dossier doit contenir :

```text
custom_components/epever_local/
  __init__.py
  client.py
  config_flow.py
  manifest.json
  sensor.py
  strings.json
  native_init.bin
  translations/
    fr.json
    en.json
```

Ne pas copier __pycache__. Redémarrer Home Assistant, puis ouvrir **Paramètres →
Appareils et services → Ajouter une intégration → EPEVER Local**.

| Paramètre | Description | Défaut |
|---|---|---|
| Adresse IP | Adresse LAN réelle de la clé | 192.168.1.100, exemple |
| Port TCP | Service natif | 8899 |
| Identifiant | Adresse Modbus configurée sur l'onduleur | 10 |
| Intervalle | Délai entre acquisitions | 5 s, plage 5–300 s |
| Batterie installée | Attribut de contexte des mesures batterie | Non |
| Panneaux installés | Attribut de contexte des mesures PV | Non |

L'assistant vérifie une lecture avant de créer l'entrée. Les capteurs sont
regroupés dans un équipement EPEVER UP5000-HM8042. Aucune modification YAML
globale ni configuration du mode TCP de la clé n'est nécessaire.

## Entités et disponibilité

L'intégration expose 21 capteurs et 5 diagnostics, soit 26 entités. Les identifiants
sont stables et liés à la passerelle, indépendamment de son adresse IP.
Les compteurs d'énergie utilisent kWh, energy et total_increasing.

Une acquisition réussie actualise le diagnostic Dernière lecture. Une erreur
rend les entités indisponibles ; les registres optionnels non pris en charge
restent indisponibles. Un zéro réellement reçu reste un zéro.

Sans batterie, le SOC brut peut valoir zéro : vérifier battery_installed avant
d'utiliser cette valeur dans une alarme. Même principe pour panels_installed.

## Exploitation

Une connexion persistante unique dessert tous les capteurs. Le temps de lecture
s'ajoute au délai configuré : pour 5 secondes, prévoir environ 6 à 7 secondes
entre deux jeux de mesures. Les erreurs déclenchent une reconnexion progressive,
avec une attente plafonnée à 60 secondes.

Fermer les autres lecteurs si la clé ne supporte pas plusieurs clients simultanés.
Pour modifier les paramètres dans cette version, supprimer puis recréer l'entrée
avec le même fichier d'initialisation. Désactiver ou supprimer l'entrée arrête
les acquisitions ; aucun réglage de l'onduleur n'est à rétablir.

La session est également conservée dans l'entrée de configuration HA. Traiter
les sauvegardes Home Assistant comme des données privées.

## Dépannage

| Symptôme | Vérifications |
|---|---|
| Intégration absente | Emplacement du dossier, manifest.json, redémarrage HA |
| Initialisation impossible | Présence du fichier, correspondance avec la clé, session complète |
| Connexion impossible | IP, TCP 8899, routage/VLAN, autres clients connectés |
| Pas de réponse Modbus | Gamme UP HI, identifiant réel, liaison série compatible |
| PV ou batterie à zéro | Présence physique de ces équipements et attributs de contexte |

Ne pas publier PCAP, initialisation native ou sauvegardes HA dans une demande de support.
