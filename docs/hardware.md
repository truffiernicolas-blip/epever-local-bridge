# Matériel et compatibilité

## Périmètre pris en charge

| Composant | Référence |
|---|---|
| Onduleur/chargeur | EPEVER UP5000-HM8042, gamme UPower-Hi, 48 V / 5 kW |
| Adaptateur | EPEVER WiFi 2.4G RJ45 D |
| Module Wi-Fi | HF-LPT270 |
| Firmware web | NW9272_LPT270_HuiNeng_V1.0.19 |
| Session native | Réponse de version V1.0.17 |
| Série | 115200 bauds, 8 bits, aucune parité, 1 bit de stop |
| Accès télémétrique | TCP 8899 |

La version retournée par la session native et celle de l'interface web sont
deux champs distincts. La compatibilité d'autres firmwares n'est pas établie.
Le protocole de session utilisé par Solar Guardian 2.2.7 est pris en charge.

## Réseau

La clé peut fonctionner en AP+STA : son point d'accès reste actif pendant sa
connexion au routeur. L'adresse AP de référence est 10.10.100.254. L'adresse LAN
est celle attribuée par le routeur ; une réservation DHCP évite son changement.

Le service natif TCP 8899 est distinct du réglage réseau TCP Client/Server visible
dans l'interface web. L'intégration utilise ce service natif sans imposer le
passage du réglage général en TCP Server. Le service HTTP utilise le port 80 ;
le support de HEAD n'est pas garanti.

## Connectique

La documentation UPower-Hi distingue le port de communication RS485 DB9 du
connecteur RJ45 BMS-Link réservé au BMS. Un connecteur RJ45 ne signifie pas
Ethernet. Utiliser le câble et l'adaptateur correspondant à la variante matérielle.

Le manuel distingue une alimentation DB9 de 5 V sur les modèles de base et
12 V sur certaines variantes RTU. Vérifier le brochage et l'alimentation avant
de raccorder un accessoire. Ne pas ajouter deux maîtres RS485 concurrents.

## Autres références

La prise en charge des eBox-WIFI-01, RJ45 A/B/C, DB9 B, Tracer et anciens UPower
n'est pas déclarée par ce projet. Le connecteur ou la marque ne suffisent pas
à établir une équivalence de protocole ou de carte de registres.

Voir les [références constructeur](references.md).
