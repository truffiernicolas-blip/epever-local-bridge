# EPEVER Local Telemetry Bridge

Intégration Home Assistant pour lire la télémétrie d'un **EPEVER UP5000-HM8042**
sur le réseau local avec une clé **EPEVER WiFi 2.4G RJ45 D**.

Le Raspberry Pi ou le serveur Home Assistant interroge directement la clé.
L'acquisition fonctionne sans compte cloud EPEVER, sans broker MQTT et sans PC
intermédiaire. Le logiciel fonctionne exclusivement en lecture seule.

## Fonctionnalités

- 26 entités réunies sous un équipement EPEVER UP5000-HM8042.
- Tensions et fréquences réseau/sortie AC, courant de sortie et énergie consommée.
- Tension, courant, puissance et énergie photovoltaïques.
- Tension, courant, SOC et code d'état batterie.
- Températures internes, bypass réseau, codes d'état et dernière lecture réussie.
- Connexion TCP persistante, contrôle CRC, timeouts et reconnexion progressive.
- Capteurs indisponibles en cas d'erreur ; aucune substitution automatique par zéro.
- Compteurs en kWh avec les métadonnées statistiques Home Assistant.

L'intervalle configuré par défaut est de 5 secondes. La cadence effective inclut
le temps des lectures séquentielles, généralement environ 6 à 7 secondes.

## Compatibilité

| Élément | Référence prise en charge |
|---|---|
| Onduleur/chargeur | EPEVER UP5000-HM8042, gamme UPower-Hi |
| Adaptateur Wi-Fi | EPEVER WiFi 2.4G RJ45 D |
| Module Wi-Fi | HF-LPT270 |
| Firmware de référence | NW9272_LPT270_HuiNeng_V1.0.19 |
| Transport local | TCP 8899 avec initialisation native puis Modbus RTU |
| Identifiant Modbus | 10 par défaut pour UP HI ; utiliser l'identifiant réel |
| Plateforme de référence | Home Assistant OS, Core 2026.10.1, Raspberry Pi 5 |

Les autres modèles et versions ne sont pas validés. Les registres UPower-Hi
diffèrent de ceux des contrôleurs Tracer. Le projet n'est pas affilié à EPEVER.

## Installation

1. Télécharger le dépôt et préparer le fichier privé **native_init.bin** de la
   passerelle, comme décrit dans le [guide d'installation](docs/home_assistant.md).
2. Copier le dossier **custom_components/epever_local**, avec native_init.bin et
   translations, dans le répertoire custom_components de Home Assistant.
3. Redémarrer Home Assistant, puis ouvrir **Paramètres → Appareils et services →
   Ajouter une intégration → EPEVER Local**.
4. Renseigner l'adresse de la clé, le port **8899**, l'identifiant de communication,
   l'intervalle et la présence éventuelle d'une batterie ou de panneaux.

L'installation est manuelle ; l'intégration n'est pas distribuée dans le catalogue
HACS par défaut. Le fichier d'initialisation est propre à la passerelle et n'est
pas livré dans le dépôt. Sa préparation requiert actuellement un fichier PCAP
local compatible ; aucun générateur universel d'initialisation n'est fourni.

## Protocole et mesures

La connexion utilise **TCP 8899**, une initialisation native de session, puis des
trames **Modbus RTU avec CRC16**, sans en-tête MBAP. L'intégration utilise uniquement
FC04 pour les registres et FC02 pour le bypass. Elle ne modifie ni l'onduleur ni
la configuration réseau de la clé.

La [spécification du protocole](docs/protocol.md) décrit les trames, les registres,
les échelles, l'ordre des mots et les limites d'interprétation.

Sans batterie ou panneaux, des registres peuvent légitimement contenir zéro.
Les attributs battery_installed et panels_installed précisent la configuration.
Un SOC nul sans batterie ne signifie pas une batterie déchargée. La puissance
active de sortie n'est pas calculée à partir du seul produit tension × courant.

## Outils

```sh
python epever_probe.py --host 192.168.1.100
python epever_probe.py --discover
python -m pip install -r requirements-capture.txt
python tools/prepare_ha.py chemin/session.pcap
python tools/analyze_solar_guardian.py chemin/session.pcap
```

La sonde TCP utilise la bibliothèque standard Python. Les outils PCAP nécessitent
Scapy. Les adresses de la documentation sont des exemples. Les rapports locaux
sont enregistrés dans reports et exclus de Git.

## Documentation

- [Matériel et compatibilité](docs/hardware.md)
- [Installation et configuration Home Assistant](docs/home_assistant.md)
- [Spécification du protocole et registres](docs/protocol.md)
- [Architecture et outils](docs/architecture.md)
- [Références techniques](docs/references.md)

## Développement

```sh
python -m unittest discover -s tests -v
python -m compileall -q src tools custom_components
```

Les tests couvrent CRC, fragmentation TCP, exceptions, restrictions de lecture,
initialisation, courant signé et compteurs d'énergie. Le workflow GitHub Actions
exécute les tests sur Python 3.11, 3.12 et 3.13. Les tests unitaires ne remplacent
pas une validation de compatibilité sur chaque variante matérielle.

## Données privées

Conserver les PCAP, native_init.bin, trames de session, numéros de série,
identifiants et sauvegardes Home Assistant hors des dépôts publics. Les octets
d'initialisation non identifiants sont traités comme des données opaques, sans
hypothèse de mot de passe universel. Les captures ne nécessitent aucun déchiffrement TLS.

Licence [MIT](LICENSE). Contributions : [CONTRIBUTING.md](CONTRIBUTING.md).
