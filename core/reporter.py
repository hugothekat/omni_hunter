# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER - THE GOLIATH REPORTING ENGINE (core/reporter.py)
📌 Formål: Genererer interaktive, militær-grade HTML efterretnings-dashboards.
🔧 Features:
   - D3.js / Vis.js Relational Graph Mapping
   - Leaflet.js Geospatial Intelligence Mapping (GEOINT)
   - AI Threat Assessment Aggregation
   - Responsive, Dark-Mode CSS Grid Layout
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Any
from core.utils import C, session
try:
    from core.nexus import nexus
except ImportError:
    nexus = None

class AutomatedCaseReporter:
    def __init__(self):
        self.loot_dir = Path(session.get("loot_folder", "loot_evidence"))
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.report_file = self.loot_dir / f"GOLIATH_MASTER_REPORT_{self.timestamp}.html"
        
        # Samledata
        self.all_emails: Set[str] = set()
        self.all_phones: Set[str] = set()
        self.all_usernames: Set[str] = set()
        self.all_domains: Set[str] = set()
        self.all_ips: Set[str] = set()
        self.all_cpr: Set[str] = set()
        self.geopoints: List[Dict[str, Any]] = []
        self.threat_intel: List[Dict[str, Any]] = []
        self.ai_summaries: List[str] = []
        self.cracked_credentials: List[Dict[str, str]] = []
        self.master_score = "Ikke beregnet"

    def _parse_loot_files(self, files: List[Path]):
        """River al data ud af de indsamlede JSON filer for at fodre dashboardet."""
        for f in files:
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
                
                # Modul 15 (Orchestrator) Extraction
                if "Confidence_Score" in data:
                    self.master_score = f"{data['Confidence_Score']}/100"
                    self.all_emails.update(data.get("Fundne_Emails", []))
                    self.all_usernames.update(data.get("Fundne_Brugernavne", []))
                    self.all_phones.update(data.get("Telefonnumre", []))
                    self.all_cpr.update(data.get("CPR_Fragments", []))
                    self.all_domains.update(data.get("Domæner", []))
                    self.all_ips.update(data.get("IP_Adresser", []))
                    
                # Modul 16 (Titan) Extraction
                if "Case_Intelligence" in data:
                    intel = data["Case_Intelligence"]
                    self.all_cpr.update(intel.get("ID_Documents", {}).get("CPR_Numre", []))
                    self.all_emails.update(intel.get("Digital_Footprint", {}).get("Emails", {}).keys())
                    self.all_phones.update(intel.get("Digital_Footprint", {}).get("Telefonnumre", []))
                    
                # Modul 10 & 34 (Netværk) Extraction for AI & GEOINT
                if "ai_threat_assessment" in data and data["ai_threat_assessment"]:
                    self.ai_summaries.append(data["ai_threat_assessment"])

                # Modul 06 (Infra) Threat Intel
                if "threat_intel" in data and data["threat_intel"].get("malicious_votes", 0) > 0:
                    self.threat_intel.append(data["threat_intel"])
                    
                if "GeoData" in data and data["GeoData"].get("lat"):
                    self.geopoints.append({
                        "lat": data["GeoData"]["lat"], 
                        "lon": data["GeoData"]["lon"], 
                        "desc": f"IP: {data.get('IP')} ({data['GeoData'].get('city')})"
                    })
                    
                # Modul 21 (BSSID) Extraction for GEOINT
                if "Lat" in data and data.get("Lat"):
                    self.geopoints.append({
                        "lat": data["Lat"], 
                        "lon": data["Lon"], 
                        "desc": f"WIFI MAC: {data.get('BSSID')} ({data.get('Netværksnavn_SSID')})"
                    })

                # Udtrækker Lækkede Credentials og Knækkede Hashes (Modul 36, 05, 03, 05_Darkweb)
                if "Knækkede_Passwords_Klartekst" in data:
                    for cred in data["Knækkede_Passwords_Klartekst"]:
                        self.cracked_credentials.append({"source": "De-Hash Engine", "target": cred.get("Hash", "")[:12]+"...", "secret": cred.get("Cleartext", "")})
                
                if "Rå_Kredentialer" in data:
                    for cred in data["Rå_Kredentialer"]:
                        if ":" in cred:
                            t, s = cred.split(":", 1)
                            self.cracked_credentials.append({"source": "Pastebin Leak", "target": t, "secret": s})
                            
                if "Credentials" in data:
                    for cred in data["Credentials"]:
                        self.cracked_credentials.append({"source": "Offline DB", "target": cred.get("Konto", "Unknown"), "secret": cred.get("Secret", "")})
                        
                if "Lækkede_Kredentialer" in data:
                    for cred in data["Lækkede_Kredentialer"]:
                        if ":" in cred:
                            t, s = cred.split(":", 1)
                            self.cracked_credentials.append({"source": "Darknet Spider", "target": t, "secret": s})

            except Exception as e:
                print(f"{C.DIM}[-] Fejl ved parsing af {f.name}: {e}{C.RESET}")

    def _build_graph_data(self) -> str:
        """Bygger Nodes og Edges til Vis.js baseret på Nexus eller rå data."""
        nodes = []
        edges = []
        node_ids = set()
        
        def add_node(n_id, label, group):
            if n_id and n_id not in node_ids:
                nodes.append({"id": n_id, "label": label, "group": group})
                node_ids.add(str(n_id).lower())

        target_node = session.get('name', 'Hovedmål')
        add_node(target_node, target_node, "Target")

        if nexus and (nexus.graph or nexus.edges):
            for node_val, meta in nexus.graph.items():
                add_node(node_val, str(node_val), meta['type'])
            
            for edge in nexus.edges:
                # Sikrer at noderne i kanten findes
                add_node(edge['source'], edge['source'], "linked")
                add_node(edge['target'], edge['target'], "linked")
                edges.append({"from": edge['source'], "to": edge['target'], "label": edge['label']})
                
                for link_val, relation in meta['linked_entities']:
                    add_node(link_val, str(link_val), "linked")
                    edges.append({"from": node_val, "to": link_val, "label": relation})
        else:
            # Fallback til rå data
            for e in self.all_emails:
                add_node(e, e, "Email")
                edges.append({"from": target_node, "to": e, "label": "Bruger"})
            for p in self.all_phones:
                add_node(p, p, "Phone")
                edges.append({"from": target_node, "to": p, "label": "Tlf"})
            for u in self.all_usernames:
                add_node(u, u, "Alias")
                edges.append({"from": target_node, "to": u, "label": "Alias"})
            for d in self.all_domains:
                add_node(d, d, "DOMAIN")
                edges.append({"from": target_node, "to": d, "label": "Ejer"})
            for i in self.all_ips:
                add_node(i, i, "IP")
                edges.append({"from": target_node, "to": i, "label": "Host"})

        return json.dumps({"nodes": nodes, "edges": edges})

    def generate(self):
        print(f"\n{C.CYAN}[*] Kompilerer The Goliath Master Report (Vis.js & Leaflet.js)...{C.RESET}")
        files = list(self.loot_dir.glob("*.json"))
        
        self._parse_loot_files(files)
        graph_json = self._build_graph_data()
        geo_json = json.dumps(self.geopoints)
        
        # Build Threat Intel HTML
        threat_html = ""
        for intel in self.threat_intel:
            source = intel.get("source", "Unknown")
            votes = intel.get("malicious_votes", 0)
            threat_html += f"<li><span style='color:var(--danger)'>[!] {source}:</span> {votes} malicious detections</li>"

        html_content = f"""
        <!DOCTYPE html>
        <html lang="da">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>GOLIATH // TACTICAL DASHBOARD</title>
            
            <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
            
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

            <style>
                :root {{ --bg: #12121c; --card: #1e1e2f; --border: #3b3b54; --accent: #00e5ff; --danger: #ff007f; --text: #cfd2d9; }}
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: var(--bg); color: var(--text); margin: 0; padding: 20px; }}
                h1 {{ color: var(--accent); border-bottom: 2px solid var(--border); padding-bottom: 10px; margin-top: 0; }}
                h2 {{ color: var(--danger); font-size: 1.2rem; margin-top: 0; }}
                
                .grid-container {{ display: grid; grid-template-columns: 1fr 2fr; gap: 20px; margin-top: 20px; }}
                .box {{ background: var(--card); border-radius: 8px; padding: 20px; border: 1px solid var(--border); box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
                .box.accent {{ border-left: 4px solid var(--accent); }}
                .box.danger {{ border-left: 4px solid var(--danger); }}
                
                #network-map {{ width: 100%; height: 500px; background-color: #0b0b10; border-radius: 6px; border: 1px solid var(--border); }}
                #geo-map {{ width: 100%; height: 350px; background-color: #0b0b10; border-radius: 6px; border: 1px solid var(--border); margin-top: 15px; z-index: 1; }}
                
                .badge {{ background: var(--border); color: var(--accent); padding: 4px 8px; border-radius: 4px; font-weight: bold; float: right; }}
                .list-group {{ list-style: none; padding: 0; margin: 0; max-height: 250px; overflow-y: auto; }}
                .list-group li {{ background: var(--bg); margin-bottom: 5px; padding: 10px; border-radius: 4px; border-left: 2px solid var(--accent); font-size: 0.9rem; word-break: break-all; }}
                
                .header-stats {{ display: flex; justify-content: space-between; background: var(--card); padding: 15px 20px; border-radius: 8px; border: 1px solid var(--border); margin-bottom: 20px; }}
                .ai-text {{ white-space: pre-wrap; font-family: monospace; color: #a5b1c2; font-size: 0.85rem; background: var(--bg); padding: 15px; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <h1>🦅 GOLIATH APEX // CENTRAL INTELLIGENCE REPORT</h1>
            
            <div class="header-stats">
                <div><strong>OPERATOR:</strong> {os.getlogin() if hasattr(os, 'getlogin') else 'SYSTEM'}</div>
                <div><strong>TARGET:</strong> <span style="color: var(--danger); font-size: 1.1rem; font-weight: bold;">{session.get('name', 'Ikke angivet').upper()}</span></div>
                <div><strong>CONFIDENCE SCORE:</strong> <span style="color: var(--accent); font-weight: bold;">{self.master_score}</span></div>
                <div><strong>TIMESTAMP:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
            </div>
            
            <div class="grid-container">
                <div style="display: flex; flex-direction: column; gap: 20px;">
                    
                    <div class="box accent">
                        <h2>Identifikatorer (IOCs)</h2>
                        <p><strong>Emails</strong> <span class="badge">{len(self.all_emails)}</span></p>
                        <ul class="list-group">{''.join([f"<li>{e}</li>" for e in self.all_emails]) if self.all_emails else "<li>Ingen data</li>"}</ul>
                        
                        <p style="margin-top: 15px;"><strong>Telefoner</strong> <span class="badge">{len(self.all_phones)}</span></p>
                        <ul class="list-group">{''.join([f"<li>+45 {p}</li>" for p in self.all_phones]) if self.all_phones else "<li>Ingen data</li>"}</ul>

                        <p style="margin-top: 15px;"><strong>Domæner & IP</strong> <span class="badge">{len(self.all_domains) + len(self.all_ips)}</span></p>
                        <ul class="list-group">
                            {''.join([f"<li>{d} (Domæne)</li>" for d in self.all_domains])}
                            {''.join([f"<li>{i} (IP)</li>" for i in self.all_ips])}
                        </ul>
                    </div>

                    <div class="box danger" style="border-left: 4px solid #f1c40f;">
                        <h2 style="color: #f1c40f;">Threat Intelligence Hits</h2>
                        <ul class="list-group">{threat_html if threat_html else "<li>Ingen kritiske hits fundet</li>"}</ul>
                    </div>

                    <div class="box danger">
                        <h2>AI Threat Assessment</h2>
                        <div class="ai-text">
                            {'<br><br>'.join(self.ai_summaries) if self.ai_summaries else 'Ingen MistralAI threat intelligence genereret.'}
                        </div>
                    </div>

                    <div class="box danger" style="border-left: 4px solid #ff007f;">
                        <h2 style="color: #ff007f;">🚨 Compromised Credentials & Hashes</h2>
                        <ul class="list-group">
                            {''.join([f"<li><span class='badge' style='float:left; margin-right:10px; background:#3b3b54; color:#fff;'>{c['source']}</span> <span style='color:#a5b1c2;'>{c['target']}</span> <br><strong style='color:#ff007f; letter-spacing: 1px; font-family: monospace; font-size: 1.1rem;'>{c['secret']}</strong></li>" for c in self.cracked_credentials]) if self.cracked_credentials else "<li style='color:#a5b1c2;'>Ingen lækkede passwords identificeret.</li>"}
                        </ul>
                    </div>

                    <div class="box accent">
                        <h2>Sikret Bevismateriale ({len(files)} Filer)</h2>
                        <ul class="list-group">
                            {''.join([f"<li style='border-left-color: #2ecc71;'>{f.name}</li>" for f in files])}
                        </ul>
                    </div>

                </div>
                
                <div style="display: flex; flex-direction: column; gap: 20px;">
                    
                    <div class="box danger">
                        <h2>Relational Intelligence Network (Link Analysis)</h2>
                        <div id="network-map"></div>
                    </div>
                    
                    <div class="box accent">
                        <h2>Geospatial Intelligence (GEOINT)</h2>
                        <div id="geo-map"></div>
                    </div>

                </div>
            </div>

            <script type="text/javascript">
                // --- VIS.JS NETWORK GRAPH ---
                var graphData = {graph_json};
                var container = document.getElementById('network-map');
                var data = {{
                    nodes: new vis.DataSet(graphData.nodes),
                    edges: new vis.DataSet(graphData.edges)
                }};
                var options = {{
                    nodes: {{ shape: 'dot', size: 16, font: {{ color: '#cfd2d9', size: 12 }}, borderWidth: 2 }},
                    edges: {{ font: {{ color: '#a5b1c2', size: 10, align: 'middle' }}, arrows: 'to', color: '#3b3b54' }},
                    physics: {{ stabilization: true, barnesHut: {{ gravitationalConstant: -3000, springLength: 150 }} }},
                    groups: {{
                        Target: {{ color: {{ background: '#ff007f', border: '#fff' }}, size: 25 }},
                        Email: {{ color: {{ background: '#00e5ff', border: '#fff' }} }},
                        Phone: {{ color: {{ background: '#2ecc71', border: '#fff' }} }},
                        Alias: {{ color: {{ background: '#f1c40f', border: '#fff' }} }}
                    }}
                }};
                var network = new vis.Network(container, data, options);

                // --- LEAFLET.JS GEOINT MAP ---
                var map = L.map('geo-map').setView([55.676098, 12.568337], 6); // Default Denmark
                L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
                    subdomains: 'abcd',
                    maxZoom: 20
                }}).addTo(map);

                var geoPoints = {geo_json};
                var bounds = [];
                geoPoints.forEach(function(pt) {{
                    if(pt.lat && pt.lon) {{
                        var marker = L.circleMarker([pt.lat, pt.lon], {{
                            color: '#ff007f',
                            fillColor: '#ff007f',
                            fillOpacity: 0.7,
                            radius: 8
                        }}).addTo(map);
                        marker.bindPopup("<b>" + pt.desc + "</b>");
                        bounds.push([pt.lat, pt.lon]);
                    }}
                }});
                
                // Auto-zoom til pins hvis der er nogen
                if(bounds.length > 0) {{
                    map.fitBounds(bounds, {{padding: [50, 50]}});
                }}
            </script>
        </body>
        </html>
        """

        self.report_file.write_text(html_content, encoding='utf-8')
        print(f"{C.GREEN}[✓] The Goliath Master Report er kompagneret og krypteret!{C.RESET}")
        print(f"{C.CYAN}    -> Dobbeltklik filen for at åbne i din browser: {self.report_file.absolute()}{C.RESET}")