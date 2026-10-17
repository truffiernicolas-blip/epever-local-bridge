# Diagnostic des protocoles

> Les adresses LAN et noms Wi-Fi de ce document sont anonymisés et illustratifs.

**Mise à jour après capture Android :** le chemin natif **TCP 8899 + initialisation
de session + Modbus RTU, unité 10** fonctionne depuis Python sur le LAN. Voir
[la preuve de lecture](capture-2026-10-17.md). Les hypothèses ci-dessous décrivent
le point de départ de l'investigation, avant cette preuve.

## Hypothèses à distinguer

| Transport / protocole | Preuve attendue | Statut actuel |
|---|---|---|
| Modbus RTU sur TCP | Trames avec CRC RTU valide et réponse corrélée | Plausible RJ45 D, non testé ici |
| Modbus TCP natif | En-tête MBAP, transaction et longueur cohérents | Non confirmé |
| TCP propriétaire | Enveloppe et sessions reproductibles | Inconnu |
| UDP propriétaire | Capture des datagrammes et réponse de service | Inconnu |
| HTTP local | Réponse HTTP et interface accessible | À sonder |
| Série encapsulée | Analyse structurée de plusieurs messages | Inconnu |
| Cloud | Flux DNS/TCP/UDP observés côté passerelle | Aucune capture fournie |

502, 8088 et 9999 sont seulement des candidats. Aucun protocole n'est inféré
automatiquement du numéro de port. La sonde actuelle ne transmet aucune fonction
Modbus. Un futur transport autorisera seulement les lectures prévues ; les réponses
devront vérifier identifiant, fonction, longueur, transaction ou CRC et exceptions.

## Carte de registres

Avant la capture, aucun registre n'était validé par une réponse de cet exemplaire.
Les premiers registres réseau/sortie AC sont désormais lus en Python, avec CRC valide.
Pour les autres mesures,
des mesures PV, batterie, AC, réseau et diagnostic demandées, adresse, fonction,
nombre de mots, signe, ordre des mots, échelle, unité et valeur sentinelle restent
à confirmer. L'existence d'un SOC ou d'un compteur ne sera pas présumée.
Ne pas convertir les adresses 3xxxx/4xxxx sans vérifier la convention du document.
Ne pas calculer une puissance, un SOC ou une énergie à partir d'autres grandeurs
sans méthode et limites explicites. Les valeurs absentes resteront indisponibles.

Le décodeur futur sera séparé du transport et sélectionné par modèle/version de
carte confirmés. Une exception Modbus prouve éventuellement un interlocuteur
Modbus, pas la signification physique des registres.

## Captures sur un réseau contrôlé

Sur une passerelle/routeur ou un port miroir qui voit effectivement le trafic de
la clé (un PC ordinaire sur un switch ne voit pas nécessairement ses flux cloud) :

```sh
tcpdump -i eth0 -nn -s 0 -w epever.pcap host 192.168.1.100
```

Remplacer interface et IP ; arrêter après une courte fenêtre représentative.
Wireshark : filtre d'affichage `ip.addr == 192.168.1.100`, puis examiner
Conversations, DNS et sens des connexions. Ne pas intercepter TLS ni extraire
de secrets. Les fichiers bruts peuvent néanmoins contenir des données sensibles.

```sh
python epever_probe.py --host 192.168.1.100 --offline --pcap epever.pcap
```

Scapy lit le fichier hors ligne : flux, compteurs et noms DNS uniquement. Pas de
réassemblage TCP, d'extraction de secrets ni de décodeur binaire à ce stade.
L'absence de paquets ne prouve pas l'absence de service. Le scan UDP générique
n'est pas implémenté : le silence UDP ne permet pas de conclure qu'un port est fermé.

## Document UP-HI retrouvé et outil de lecture ponctuelle

Une [copie du document UP-HI V8.5](https://forum.iobroker.net/assets/uploads/files/1667825519362-up-hi-communication-protocol-v8.5.pdf)
est désormais accessible (hébergement tiers ; version effective de l'onduleur à confirmer).
Extraits utiles, fonction **04**, adresses hexadécimales :

| Mesure candidate | Adresse | Décodage documentaire |
|---|---|---|
| Tension réseau | 3500 | uint16 /100 V |
| Tension AC sortie | 3521 | uint16 /100 V |
| Tension PV | 3549 | uint16 /100 V |
| Courant PV | 354A | uint16 /100 A |
| Puissance PV | 354B–354C | mots bas/haut, /100 W |
| Énergie PV cumulée | 3557–3558 | mots bas/haut, /100 kWh |
| Tension batterie | 3580 | uint16 /100 V |
| Courant batterie | 3581–3582 | signé, mots bas/haut, /100 A ; charge positive |
| SOC | 3586 | uint16 % |

Ces interprétations ne sont pas validées sur le matériel de l'utilisateur.
L'outil ne publie donc pas ces grandeurs comme des mesures acquises.

```sh
python tools/read_inputs.py --host 192.168.1.100 --port 9999 --unit 10 --address 0x3580
```

Utiliser seulement si le serveur TCP est activé. Le code ne construit que des
requêtes FC04, interdit l'adresse broadcast, limite à 16 registres, contrôle CRC,
identifiant, fonction et longueur, et gère la fragmentation TCP. Le rapport
contient les trames de cette lecture, pas d'identifiants réseau. Une adresse et
une unité doivent être choisies d'après le matériel ; pas de balayage automatique.
