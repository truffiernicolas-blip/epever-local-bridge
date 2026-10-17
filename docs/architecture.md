# Architecture et outils

## Intégration Home Assistant

| Module | Responsabilité |
|---|---|
| client.py | Session native, lectures autorisées, CRC et décodage |
| __init__.py | Coordinateur d'acquisition, reconnexion et cycle de vie |
| config_flow.py | Configuration locale et validation de connexion |
| sensor.py | Entités, unités, statistiques et attributs de contexte |
| translations | Libellés de l'assistant |

Le coordinateur partage un client entre les entités. Un verrou empêche les
acquisitions concurrentes. Les blocs de registres autorisés sont fixes ; aucune
API d'écriture n'est exposée. La connexion est fermée au déchargement ou à l'arrêt.

## Utilitaires autonomes

| Commande | Fonction |
|---|---|
| epever_probe.py --host IP | Sonde TCP séquentielle, rapport JSON |
| epever_probe.py --discover | Lecture du cache ARP local, candidats non identifiés |
| tools/prepare_ha.py PCAP | Préparation privée de native_init.bin |
| tools/analyze_solar_guardian.py PCAP | Analyse structurée d'une session native |
| tools/analyze_solar_guardian.py PCAP --live-host IP | Acquisition FC04 ponctuelle avec initialisation |
| tools/read_inputs.py | Lecture FC04 brute sur un transport RTU/TCP déjà disponible |

La sonde teste 80, 443, 502, 8088, 8899 et 9999 par défaut. Aucun protocole
n'est déduit du numéro de port. L'option --http-ports autorise explicitement HEAD ;
le client ne suit pas de redirection et ne s'authentifie pas.

L'analyse générique --pcap de la sonde exporte seulement les métadonnées de flux
et noms DNS. L'analyseur Solar Guardian réassemble les deux sens TCP, contrôle
les CRC et associe les lectures aux réponses. Il refuse les trous de séquence et
les formats inconnus. Son appariement est ciblé sur les sessions prises en charge,
pas sur un trafic Modbus arbitraire avec plusieurs requêtes simultanées.

Les rapports sont privés et écrits dans reports. Les outils n'implémentent ni
scan UDP générique, ni reconfiguration automatique, ni déchiffrement TLS.

## Développement

Les tests unitaires utilisent des trames synthétiques et serveurs TCP locaux.
Aucune capture, donnée de session réelle, connexion à un onduleur ou installation
Home Assistant n'est nécessaire pour les exécuter. Le pipeline vérifie aussi la
compilation syntaxique des modules.

Un service MQTT autonome et un déploiement Docker ne font pas partie de cette
version. L'intégration native assure directement l'acquisition dans Home Assistant.
