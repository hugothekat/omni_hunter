# -*- coding: utf-8 -*-
"""
Nexus Graph Engine for Omni Hunter
Håndterer Entity Resolution og dynamisk opbygning af relationelle grafer.
Fuldt integreret med GOLIATH V8 arkitekturen.
"""
import uuid
from enum import Enum
from typing import Dict, List, Optional
from core.logger import logger

class EntityType(Enum):
    PERSON = "PERSON"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    DOMAIN = "DOMAIN"
    IP = "IP"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    CREDENTIAL = "CREDENTIAL"
    SOCIAL = "SOCIAL"
    BSSID = "BSSID"
    UNKNOWN = "UNKNOWN"

class NexusGraph:
    """
    Central hub for OSINT entity resolution and graph linking.
    """
    def __init__(self):
        # graph: map fra normaliseret node_val til metadata dictionary
        self.graph: Dict[str, dict] = {} 
        self.edges: List[dict] = []
        
        # NYT V43: Adjacency list til hurtig opslag i Reporteren
        self.adjacency: Dict[str, List[tuple]] = {}
        
        logger.info("[NEXUS] Graph Engine initialiseret i hukommelsen.")

    def ingest(self, entity_type: EntityType, value: str, source: str = "Unknown", confidence: float = 1.0) -> None:
        """
        Indlæser en entitet i Nexus Graph. Undgår dubletter og opdaterer confidence/sources.
        """
        if not value:
            return

        # Normaliserer nøglen for at forhindre at "Email@Test.com" og "email@test.com" bliver to noder.
        value_key = str(value).strip().lower()
        
        if value_key not in self.graph:
            self.graph[value_key] = {
                "id": str(uuid.uuid4()),
                "type": entity_type.value,
                "label": str(value).strip(), # Beholder original casing til UI'en
                "sources": [source],
                "confidence": confidence,
                "first_seen": source,
                "linked_entities": [] # Til reporterens fallback
            }
            logger.debug(f"[NEXUS] Ingested NEW Node: [{entity_type.value}] {value} (Source: {source})")
        else:
            # Hvis noden eksisterer, appender vi blot kilden for at opbygge et stærkere bevismateriale.
            if source not in self.graph[value_key]["sources"]:
                self.graph[value_key]["sources"].append(source)
            # Vi opdaterer tilliden til den maksimale confidence-værdi identificeret.
            self.graph[value_key]["confidence"] = max(self.graph[value_key]["confidence"], confidence)

    def link(self, source_val: str, target_val: str, label: str) -> None:
        """
        Opretter en relation (edge) mellem to kendte entiteter i grafen.
        """
        if not source_val or not target_val:
            return

        src_key = str(source_val).strip().lower()
        tgt_key = str(target_val).strip().lower()

        # Hvis modulet forsøger at linke til en node, der ikke formelt er indlæst (ingested),
        # auto-genererer vi noderne som UNKNOWN for at bevare grafens integritet og forhindre UI-crashes.
        if src_key not in self.graph:
            self.ingest(EntityType.UNKNOWN, source_val, source="Linker-Auto")
            logger.warning(f"[NEXUS] Auto-created UNKNOWN node for source linking: {source_val}")
            
        if tgt_key not in self.graph:
            self.ingest(EntityType.UNKNOWN, target_val, source="Linker-Auto")
            logger.warning(f"[NEXUS] Auto-created UNKNOWN node for target linking: {target_val}")
        
        edge = {
            "source": src_key,
            "target": tgt_key,
            "label": label
        }
        
        # Check for dublet-kanter for at undgå at UI'en tegner den samme linje flere gange.
        if edge not in self.edges:
            self.edges.append(edge)
            
            # Opdaterer linked_entities for Reporterens _build_graph_data
            if (tgt_key, label) not in self.graph[src_key]["linked_entities"]:
                self.graph[src_key]["linked_entities"].append((tgt_key, label))
            logger.debug(f"[NEXUS] Linked: {source_val} --[{label}]--> {target_val}")

    def predict_links(self) -> List[dict]:
        """
        GOLIATH V54: Graph-based Predictive Linking.
        Scanner grafen for targets/personas der deler IP'er, netværk eller lokationer.
        """
        predictions = []
        shared_nodes = {}
        
        # Identificerer delte enheder (f.eks. en IP-adresse to targets har ramt)
        for edge in self.edges:
            src = edge['source']
            tgt = edge['target']
            if tgt in self.graph and self.graph[tgt]['type'] in [EntityType.IP.value, EntityType.LOCATION.value, EntityType.BSSID.value]:
                if tgt not in shared_nodes:
                    shared_nodes[tgt] = set()
                shared_nodes[tgt].add(src)
                
        # Forudsiger forbindelser mellem kilderne
        for shared_node, sources in shared_nodes.items():
            if len(sources) > 1:
                src_list = list(sources)
                for i in range(len(src_list)):
                    for j in range(i+1, len(src_list)):
                        pred_edge = {"source": src_list[i], "target": src_list[j], "label": f"Forudsagt: Deler {self.graph[shared_node]['type']}"}
                        
                        # Undgå dubletter af allerede eksisterende kanter
                        if not any((e['source'] == pred_edge['source'] and e['target'] == pred_edge['target']) or (e['source'] == pred_edge['target'] and e['target'] == pred_edge['source']) for e in self.edges + predictions):
                            predictions.append(pred_edge)
        return predictions

# GOLIATH Nexus global instans (Singleton)
nexus = NexusGraph()
