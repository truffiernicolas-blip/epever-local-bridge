# Contrat prévu pour Home Assistant

> Les adresses LAN et noms Wi-Fi de ce document sont anonymisés et illustratifs.

## Installation vérifiée sur le Raspberry

Les fichiers ont été transférés avec File editor dans un dossier neuf
`/homeassistant/custom_components/epever_local`, sans modifier `configuration.yaml`
ni HACS. Home Assistant a été redémarré (aucune automatisation en cours signalée
par son dialogue), puis l'intégration a été ajoutée depuis Appareils et services.
Le test de connexion depuis HA et l'acquisition périodique ont réussi.

- Appareil : **EPEVER UP5000-HM8042**, intégration **EPEVER Local 0.1.0**.
- Serveur : 192.168.1.10 ; clé : 192.168.1.100:8899 ; unité 10 ; intervalle 5 s.
- 26 entités, dont 21 capteurs et 5 diagnostics ; aucune commande de pilotage.
- Valeurs observées : réseau/sortie environ 247 V, sortie 1,43–1,48 A,
  fréquences 50 Hz, énergie sortie 43,37 kWh, températures 29–35 °C,
  mode bypass réseau. PV et batterie à zéro, matériel absent comme déclaré.
- Mises à jour observées à 20:15:17, 24, 30, 36, 42 et 49 Europe/Paris :
  cadence effective 6–7 s, temps des lectures séquentielles compris.
- Les 16 tests Python et la compilation syntaxique ont réussi. La validation
  sur HA confirme aussi le chargement des modules et la création des entités.

Accès appareil :
Paramètres → Appareils et services → EPEVER Local → appareil EPEVER.
Le dashboard principal existant n'a pas été modifié. Le SOC à zéro est la valeur
brute de l'onduleur : `battery_installed: false` précise qu'aucune batterie n'est
présente. Ne pas créer d'alarme batterie faible sur ce zéro sans vérifier cet attribut.

## Déploiement direct préparé le 17 octobre 2026

L'installation observée est Home Assistant OS sur Raspberry Pi 5, serveur
192.168.1.10, Core 2026.10.1, Supervisor 2026.10.2, OS 18.3. File editor et
Advanced SSH & Web Terminal sont déjà installés ; aucun Mosquitto n'est listé.

Pour répondre au souhait de faire interroger directement la clé par HA, une
intégration native `custom_components/epever_local` a été créée. Elle utilise
TCP 8899, unité 10, session persistante, lectures FC04 et lecture seule FC02 pour
le bypass. Intervalle par défaut : 5 secondes. Aucune écriture dans l'onduleur.
Un coordinateur unique sérialise les lectures et reconnecte avec attente
progressive après panne ; une mesure manquante reste indisponible, pas zéro.
Les données numériques reçues à zéro restent affichables, avec attributs
indiquant l'absence de batterie/panneaux configurée par l'utilisateur.

Le fichier privé `native_init.bin` est issu de la capture de ce dongle, exclu
de Git. Il doit être conservé pour une nouvelle configuration. La session est
également enregistrée dans l'entrée d'intégration HA ; sauvegarder la configuration
HA comme donnée privée. Aucun compte ni mot de passe cloud n'est requis.

Installation manuelle : copier le dossier `epever_local` dans `custom_components`,
avec `native_init.bin` et `translations`, redémarrer HA, puis ajouter **EPEVER
Local** dans Appareils et services. Adresse 192.168.1.100, port 8899, unité 10,
intervalle 5 s. Les mesures apparaissent sous un équipement UP5000-HM8042.
Pour revenir en arrière, supprimer l'entrée d'intégration via HA ; le client est
fermé à son déchargement. Aucun réglage de la clé n'a besoin d'être rétabli.

Le contrat MQTT ci-dessous reste une alternative prévue ; MQTT n'est pas nécessaire
pour ce déploiement natif, et aucun broker n'a été installé pour l'occasion.

Document de conception ; aucun publisher MQTT ni acquisition périodique encore
implémenté dans le bridge MQTT. L'acquisition périodique est implémentée dans
l'intégration native décrite ci-dessus.

Un équipement `EPEVER UP5000-HM8042`, avec identifiant configuré stable indépendant
de l'IP, regroupera uniquement les mesures validées. Chaque entité aura unique_id,
unité, device_class appropriée et state_class adaptée. Les valeurs instantanées
utiliseront `measurement`. Les compteurs d'énergie utiliseront Wh/kWh et `energy`,
avec `total` ou `total_increasing` selon leur comportement de remise à zéro
effectivement vérifié. Une puissance en W seule ne constitue pas un compteur
d'énergie pour le tableau de bord Énergie.
[Classes de capteurs officielles](https://contributors.home-assistant.io/core/entities/sensor/).

Prévoir disponibilité avec testament MQTT, expiration des mesures, horodatage UTC
de dernière lecture réussie et republication de Discovery au redémarrage de HA
ou conservation des configurations. Une erreur n'enverra pas zéro comme mesure.
[MQTT Discovery officiel](https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery).

Le service futur utilisera une seule connexion à la clé, un intervalle par défaut
de 5 s configurable, des timeouts, un recul progressif après panne et un verrou
empêchant les lectures simultanées dans le processus. Les autres applications
devront libérer la clé. Les identifiants MQTT resteront hors logs et dépôt.
