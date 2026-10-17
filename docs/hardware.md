# Identification matérielle — 17 octobre 2026

> Les adresses LAN et noms Wi-Fi de ce document sont anonymisés et illustratifs.

Mise à jour : accès télémétrique natif **TCP 8899** confirmé après analyse du
PCAP Android et initialisation de session. [Résultats](capture-2026-10-17.md).

## Établi

La photo fournie par l'utilisateur porte lisiblement **EPEVER WIFI 2.4G RJ45 D**.
Le QR code et le numéro individuel ne sont pas reproduits ici. La photo n'identifie
ni la version firmware ni le câblage vers l'onduleur.

L'UP5000-HM8042 est déclaré par l'utilisateur, pas encore vérifié sur son étiquette.
La fiche UPower-Hi répertorie ce modèle en 48 V, 5 kW ; ne pas le confondre avec
la gamme UPower antérieure ou les modèles 110 V.
[Fiche officielle](https://www.epever.com/upload/file/2104/EPEVER-Datasheet-UPower-Hi.pdf).

## Connectique à confirmer avant branchement

Le manuel UPower-Hi distingue un port de communication RS485 DB9 et un RJ45
BMS-Link réservé à cette fonction. Il distingue aussi une alimentation DB9
5 V/0,2 A sur la version de base et 12 V/0,2 A sur la variante RTU.
Un connecteur RJ45 n'est donc pas une preuve d'Ethernet ni d'interchangeabilité.
La liaison exacte et tout adaptateur DB9–RJ45 doivent être identifiés sur
l'installation existante avant de proposer un autre câble.
[Manuel officiel V2.6, section interfaces](https://www.epever.com/wp-content/uploads/2021/09/UPower-Hi-Manual-EN-V2.6.pdf).

La fiche officielle DB9 B annonce 5 V et le protocole IoT EPEVER V1.1 : même au
sein de la marque, le nom et le connecteur comptent.
[Fiche DB9 B](https://www.epever.com/wp-content/uploads/2021/08/EPEVER-Datasheet-EPEVER-WiFi-2.4G-DB9-B.pdf).

## Informations manquantes

- Adresse IP et entrée DHCP correspondant à la clé.
- Version firmware, mode TCP actuel, destination/port distant et paramètres série,
  relevés dans une interface locale si accessible, sans sauvegarder de changement.
- Étiquette complète de l'onduleur et adaptateur/câble utilisé vers la clé.
- Type d'installation Home Assistant : OS, Container ou autre, pour le déploiement.

Aucun flashage, reset, changement série ou modification réseau n'a été effectué.

## Vérifications réelles du 17 octobre 2026

Après un balayage Wi-Fi explicite Windows (la première liste était en cache),
connexion réussie à l'AP avec le mot de passe usine. IP attribuée au PC :
10.10.100.150 ; passerelle : 10.10.100.254.

Lecture authentifiée de l'interface web, puis retour du PC sur `WIFI_LOCAL` :
la même interface est accessible à **192.168.1.100**. La MAC observée en ARP
correspond à celle de l'AP et de la page d'état. La connexion au routeur est
donc vérifiée, même si l'AP reste actif.

- Module déclaré par son interface : HF-LPT270.
- Version déclarée : NW9272_LPT270_HuiNeng_V1.0.19.
- Mode Wi-Fi actuel : APSTA ; SSID station : WIFI_LOCAL ; DHCP activé.
- Série relevée : 115200, 8 bits, sans parité, 1 stop, sans contrôle de flux.
- Réseau applicatif : TCP CLIENT, destination configurée **192.168.1.20:15000**,
  timeout déclaré 0. Destination locale, pas le domaine cloud cité dans le projet
  tiers ; son rôle et son fonctionnement restent inconnus.
- TCP 80 ouvert, HTTP confirmé par GET authentifié. HEAD ne donne pas de réponse
  exploitable sur cet équipement.
- 443/502/8088/9999 : délais dépassés lors de la sonde, pas une preuve de fermeture.

Les pages de configuration lues sont conservées dans `reports/` (ignoré par Git).
Elles sont privées et peuvent contenir des secrets ; ne pas les publier.
Le mot de passe Wi-Fi fourni dans le chat n'a pas été recopié dans la documentation.
Aucune écriture de configuration n'a été effectuée : la connexion demandée était
déjà opérationnelle. Aucun redémarrage de la clé et aucune lecture Modbus.
