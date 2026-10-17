# Protocole local RJ45 D / UPower-Hi

## Transport

Le service natif est un flux **TCP sur le port 8899**. Après initialisation de
session, il transporte des trames **Modbus RTU avec CRC16**, sans en-tête MBAP.
Le client conserve la connexion pour les acquisitions successives.

L'adresse AP de référence est 10.10.100.254 ; sur le LAN, utiliser l'adresse
attribuée à la clé. Ce service est distinct des paramètres du canal TCP
Client/Server général. Un accès Modbus TCP standard ne remplace pas cette session.

## Initialisation native

| Requête | Taille | Signification |
|---|---|---|
| Type | 1 octet | 0x10 |
| Longueur | 1 octet | 0x1E, taille des données qui suivent |
| Longueur identifiant | 2 octets, big-endian | 0x0016 |
| Identifiant passerelle | 22 octets | Numéro de série ASCII |
| Suffixe | 6 octets | Données opaques propres au format pris en charge |

La requête prise en charge mesure 32 octets. Le projet ne suppose pas que le
suffixe soit une constante ou un mot de passe universel. L'initialisation est
importée comme une trame opaque, conservée hors du dépôt et envoyée avant les lectures.

La réponse commence par 0x20 et une longueur sur un octet. Le corps contient
une longueur de chaîne big-endian sur deux octets, puis une chaîne ASCII de
version. Le format de référence retourne V1.0.17. Ce champ n'est pas la version
du firmware de l'interface web.

## Trames Modbus

Une requête FC04 contient : unité, fonction 0x04, adresse 16 bits big-endian,
nombre de registres 16 bits big-endian et CRC16 Modbus little-endian.
Chaque registre de réponse contient un mot 16 bits big-endian.

L'identifiant de référence UPower-Hi est **10**. L'adresse réelle configurée sur
l'onduleur prévaut. L'intégration utilise uniquement **FC04** et **FC02** ;
aucune fonction d'écriture n'est implémentée.

La réponse est contrôlée sur l'identifiant, la fonction, la taille et le CRC.
Les exceptions Modbus sont distinguées d'une trame invalide. Les lectures sont
séquentielles ; une réponse invalide ou un timeout ferme la session avant reconnexion.

## Carte de registres implémentée

Toutes les adresses ci-dessous sont hexadécimales, directement utilisées dans
les requêtes. Les valeurs 32 bits occupent le mot bas à l'adresse de départ,
puis le mot haut à l'adresse suivante. Leur valeur est low | (high << 16).

| Adresse | Mesure | Type | Échelle / unité |
|---|---|---|---|
| 3500 | Tension réseau | uint16 | /100 V |
| 3501 | Courant de charge réseau | uint16 | /100 A |
| 3502–3503 | Puissance de charge réseau | uint32 | /100 W |
| 3504 | Fréquence réseau | uint16 | /100 Hz |
| 350F–3510 | Énergie cumulée de charge réseau | uint32 | /100 kWh |
| 3511 | Code état charge réseau | uint16 | Brut |
| 3513–3514 | Températures chargeur / puissance | int16 | /100 °C |
| 3521 | Tension sortie AC | uint16 | /100 V |
| 3522 | Courant sortie AC | uint16 | /100 A |
| 3523 | Code état sortie AC | uint16 | Brut |
| 3529 | Fréquence sortie AC | uint16 | /100 Hz |
| 3530–3531 | Énergie cumulée sortie AC | uint32 | /100 kWh |
| 3532–3533 | Températures dissipateurs 1 / 2 | int16 | /100 °C |
| 3549 | Tension PV | uint16 | /100 V |
| 354A | Courant PV | uint16 | /100 A |
| 354B–354C | Puissance PV | uint32 | /100 W |
| 3557–3558 | Énergie cumulée PV | uint32 | /100 kWh |
| 3559 | Code état PV | uint16 | Brut |
| 3580 | Tension batterie | uint16 | /100 V |
| 3581–3582 | Courant batterie | int32 | /100 A, positif en charge |
| 3586 | SOC batterie | uint16 | % |
| 3589 | Code état batterie | uint16 | Brut |
| 2100, FC02 | Bypass réseau | Bit | 1 : bypass, 0 : sans bypass |

Le SOC hors de la plage 0–100 est indisponible. Les sentinelles de température
0x7FFF et 0xFFFF sont traitées comme indisponibles. Les codes d'état sont exposés
bruts ; aucune traduction complète des alarmes n'est fournie.

Le décodage s'appuie sur la carte UP-HI V8.5 et l'implémentation du client. La
lecture des registres ne valide pas l'exactitude métrologique de chaque grandeur
sur toutes les variantes. La plage non nulle de courant batterie, le SOC et les
mesures photovoltaïques requièrent une validation avec les équipements concernés.

## Règles d'interprétation

Les zéros reçus ne sont pas assimilés à une panne de communication. Les registres
absents ne sont pas remplacés par zéro. L'état sans batterie doit être pris en
compte avant d'interpréter le SOC. Les énergies proviennent des compteurs exposés,
sans intégration logicielle de la puissance. Aucune puissance active de sortie
n'est déduite du produit tension × courant.

Voir les [références techniques](references.md) et le client
custom_components/epever_local/client.py pour les plages de lecture autorisées.
