# Investigation comparative — 17 octobre 2026

> Les adresses LAN et noms Wi-Fi de ce document sont anonymisés et illustratifs.

**Résultat ultérieur : preuve de concept réussie en Python sur le LAN**, via le
port natif 8899 sans reconfiguration de la clé. Voir [l'analyse de capture](capture-2026-10-17.md).
Les conclusions provisoires ci-dessous retracent l'investigation avant cette preuve.

## Conclusion provisoire

Conserver la **RJ45 D identifiée par photo** est la piste prioritaire. Un accès
local RTU sur TCP est documenté par un projet ayant testé cette référence.
Cela ne prouve ni la disponibilité actuelle du serveur sur cette clé, ni la
compatibilité de la carte de registres avec l'UP5000-HM8042.
Les conclusions portent sur les sources consultées, pas sur des mesures de
l'installation : aucune communication avec le matériel réel n'a encore eu lieu.

## Comparaison

| Solution | Preuve disponible | Limite pour cette installation | Décision |
|---|---|---|---|
| RJ45 D existante, serveur TCP | `ha-epever` teste Tracer AN + RJ45 D, RTU sur TCP | Firmware, configuration et carte UP-Hi à vérifier | Priorité |
| eBox-WIFI-01 | Ancienne passerelle RS485/Wi-Fi ; réglages STA décrits par un auteur | Ce n'est pas la clé photographiée | Référence historique |
| DB9 B / autres clés 2.4G | Références et protocoles officiels distincts | Aucune équivalence firmware établie | Ne pas transposer |
| RS485–USB | Accès série direct, réalisable en principe | Câblage, isolation et maître unique ; remplacement de la clé à étudier | Repli simple |
| RS485–Ethernet | Transport local indépendant du cloud | Choix RTU transparent ou Modbus TCP à expliciter | Repli réseau |
| ESP32 + RS485 | Architecture ouverte personnalisable | Développement et validation électriques supplémentaires | Repli plus coûteux en travail |
| Redirection cloud vers serveur local | Hypothèse à étudier par capture | Format, sessions, authentification inconnus | Ne pas développer à l'aveugle |

La fiche [eBox-WIFI-01](https://www.epever.com/upload/file/1904/EPEVER-Datasheet-eBox-WIFI-01.pdf)
décrit RS485, RJ45 et 115200 bauds par défaut. Son
[avis officiel de fin de production](https://www.epever.com.cn/news/2159.html)
annonce en 2022 son remplacement par RJ45 A, sans établir une identité de protocole.
Le [projet de réglage eBox](https://github.com/gabrielpc1190/eBox-Wifi-01-hacks)
décrit une manipulation de mode STA sur son matériel : ne pas l'appliquer à la RJ45 D.

## Projets et sources techniques

[zuzkins/ha-epever](https://github.com/zuzkins/ha-epever) confirme Tracer AN + RJ45 D.
Il documente une interface web, un serveur TCP sur 9999, un seul client et un
mode cloud client vers `sg.mysolarguardian.com:15000`. Il signale que le passage
serveur peut arrêter le cloud. Ce domaine est une piste de capture, pas une
destination observée sur la clé de l'utilisateur. Le projet expose aussi des
commandes d'écriture : son installation complète n'est pas adaptée à notre
phase strictement en lecture. Ne pas importer ses registres Tracer.

[fatyogi/epever-upower-tracer](https://github.com/fatyogi/epever-upower-tracer)
sépare les modules Tracer et UPower et fournit une référence de protocole UPower.
Il ne constitue pas une validation de la variante UPower-Hi actuelle.

Le [fil initial demandé](https://community.home-assistant.io/t/epever-modbus-rs-485-config/214397)
est une piste communautaire historique (eBox/Tracer et 8088), pas une spécification
universelle. Un [autre fil UP-Hi, message 28](https://community.home-assistant.io/t/epever-upower-hi-modbus-setting-if-you-need/483184/28)
référence « UP-HI communication protocol V8.5.pdf ». Le lien Drive a échoué lors
de la consultation : contenu non vérifié, donc aucune adresse validée à partir
de ce lien. Mise à jour pendant les essais : une copie accessible du PDF a été
retrouvée sur ioBroker ; voir [le protocole](protocol.md) et [les essais réels](trials-2026-10-17.md).
Sa correspondance avec le firmware de l'onduleur reste à confirmer sur des réponses réelles.

## Reconfiguration : préparation, pas exécution

Lire et conserver hors dépôt les écrans réseau et série, la version firmware,
le mode, les ports, la destination distante et les paramètres Wi-Fi. Éviter de
partager captures contenant mots de passe, QR ou jetons. Documenter comment
revenir exactement au mode et à la destination initiaux avant le changement.
Un reset usine n'est pas une sauvegarde ni une procédure de retour suffisante.

Vérifier ensuite si le firmware de cette clé propose réellement TCP-Server et
quel port il accepte. La coexistence cloud/local n'est pas démontrée. Ne pas
promettre un fonctionnement simultané ; vérifier en essai après validation du
changement. Aucun firmware alternatif compatible n'a été validé dans cette étude.

## Validation progressive

1. A : matériel identifié partiellement ; IP, firmware, câblage et carte UP-Hi manquants.
2. B : confirmer le transport local puis lire un seul registre documenté et comparer à l'écran.
3. C : vérifier unités, ordre des mots, signe, alarmes et compteurs sur plusieurs valeurs.
4. D : publier seulement les mesures validées via MQTT Discovery.
5. E : reconnexion, obsolescence, Docker, tests et déploiement suivant le type de HA.

Sans serveur local utilisable, étudier une passerelle RS485 isolée. Ne jamais
mettre le bridge et la clé officielle en concurrence comme deux maîtres du même
bus ; un arbitrage ou un véritable proxy maître unique nécessiterait une étude.
