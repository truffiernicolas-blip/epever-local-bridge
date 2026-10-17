"""Lecture du cache voisin local ; aucune recherche de sous-réseau."""
import re
import subprocess


def neighbors():
    try:
        result = subprocess.run(["arp", "-a"], capture_output=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return {"status": "unavailable", "candidates": []}
    addresses = sorted(set(re.findall(rb"\b(?:\d{1,3}\.){3}\d{1,3}\b", result.stdout)))
    return {"status": "cache_only", "candidates": [a.decode() for a in addresses],
            "identity": "unverified", "note": "Confirmer dans les baux DHCP et sur l'etiquette ; cache incomplet."}
