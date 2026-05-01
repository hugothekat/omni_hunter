# -*- coding: utf-8 -*-
"""
🚀 GOLIATH WEB COMMAND CENTER (DJANGO MICRO-CORE)
📌 Formål: Django-server med ORM Mapping og interaktivt HTML Dashboard.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

import json
import subprocess
import threading
import glob
import socket
import django
from django.conf import settings
from core.utils import C, session

# =====================================================================
# 1. DYNAMISK DJANGO BOOTSTRAPPER (SKAL KØRES FØR MODELS IMPORTERES)
# =====================================================================
if not settings.configured:
    loot_dir = session.get("loot_folder", "workspaces/standard_sag")
    os.makedirs(loot_dir, exist_ok=True)
    # Tvinger absolut sti for at undgå 'Datalake ikke fundet' fejl under multi-threading
    db_path = os.path.abspath(os.path.join(loot_dir, "omni_datalake.db"))
    
    settings.configure(
        DEBUG=True,
        SECRET_KEY="goliath-apex-web-key-v45-classified",
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=["*"],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': db_path,
            }
        },
        INSTALLED_APPS=['core'], # Gør det muligt for Django at mappe modeller i denne fil
        MIDDLEWARE=['django.middleware.common.CommonMiddleware'],
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': False,
        }],
    )
    django.setup()

# =====================================================================
# 2. IMPORTS, DJANGO MODELS & ORM MAPPING
# =====================================================================
from django.db import models
from django.urls import path
from django.http import JsonResponse, HttpResponse
from django.template import Engine, Context
from django.core.management import execute_from_command_line
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage

class OsintRecord(models.Model):
    """GOLIATH V45: Mapper The SQLite Data Lake til Django ORM for professionel datahåndtering."""
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()
    source_module = models.CharField(max_length=255)
    target = models.CharField(max_length=255)
    data_json = models.TextField()

    class Meta:
        db_table = 'osint_records'
        managed = False  # Vi lader modulerne oprette tabellen, Django læser den bare
        app_label = 'core'

# =====================================================================
# 2.5 CELERY ASYNC TASK QUEUE (REPROHACK INTEGRATION)
# =====================================================================
try:
    from celery import Celery
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.web_server')
    celery_app = Celery('core.web_server', broker='redis://127.0.0.1:6379/0')
    celery_app.conf.update(task_serializer='json', result_serializer='json', accept_content=['json'])
    
    @celery_app.task(name="execute_goliath_module")
    def execute_goliath_module(module_id, target):
        subprocess.run([sys.executable, "main.py", "-t", target, "-m", str(module_id)])
        return f"Modul {module_id} mod {target} fuldført."
except ImportError:
    celery_app = None

# =====================================================================
# 3. VIEWS & TEMPLATES (HTML DASHBOARD)
# =====================================================================
def dashboard(request):
    """Interaktivt HTML Dashboard med Chart.js og Bootstrap (Dark Mode)."""
    error_msg = None
    records = []
    stats = {}
    query = request.GET.get('q', '').strip()
    
    try:
        if query:
            # Søger i mål, modulnavn og rå JSON beviser
            records = OsintRecord.objects.filter(
                models.Q(target__icontains=query) | 
                models.Q(source_module__icontains=query) | 
                models.Q(data_json__icontains=query)
            ).order_by('-id')[:100]
        else:
            records = OsintRecord.objects.all().order_by('-id')[:100]
            
        for r in records:
            stats[r.source_module] = stats.get(r.source_module, 0) + 1
    except Exception as e:
        error_msg = f"Data Lake er tom eller ikke initialiseret. Kør et modul i terminalen først! (Detaljer: {e})"

    html_template = """
    <!DOCTYPE html>
    <html lang="da" data-bs-theme="dark">
    <head>
        <meta charset="UTF-8">
        <title>GOLIATH // COMMAND CENTER</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { background-color: #0b0b10; color: #cfd2d9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            .navbar { background-color: #1e1e2f !important; border-bottom: 2px solid #ff007f; }
            .card { background-color: #1e1e2f; border: 1px solid #3b3b54; }
            .table { color: #cfd2d9; }
            .table-dark th { background-color: #12121c; color: #00e5ff; border-color: #3b3b54; }
            .text-accent { color: #00e5ff; }
            .text-danger-custom { color: #ff007f; }
            .dropzone { 
                border: 2px dashed #3b3b54; border-radius: 8px; padding: 20px; 
                text-align: center; color: #cfd2d9; cursor: pointer; transition: all 0.3s ease; 
            }
            .dropzone.dragover { border-color: #00e5ff; background-color: rgba(0, 229, 255, 0.1); }
            .dropzone:hover { border-color: #ff007f; }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark">
            <div class="container-fluid">
                <a class="navbar-brand text-danger-custom fw-bold" href="#">🦅 GOLIATH WEB COMMAND CENTER</a>
                <span class="navbar-text text-accent">Batch 7: Live Terminal & Master Report Download</span>
                <span class="navbar-text text-accent">Batch 9: Forensic Dropzone & Asynchronous Extraction</span>
                <a href="/graph/" class="btn btn-outline-info btn-sm ms-auto">🌐 Visualisér Intelligence Netværk</a>
            </div>
        </nav>
        <div class="container mt-4">
            {% if error_msg %}
                <div class="alert alert-danger" style="background-color: #2c0b14; border: 1px solid #ff007f; color: #ffb3d9;">
                    <strong>ADVARSEL:</strong> {{ error_msg }}
                </div>
            {% else %}
            <div class="row">
                <div class="col-md-3">
                    <div class="card p-3 mb-4" style="border-color: #ff007f;">
                        <h5 class="text-danger-custom">🚀 Celery Operation</h5>
                        <form id="triggerForm">
                            <input type="text" id="tTarget" class="form-control bg-dark text-light border-secondary mb-2" placeholder="Target (URL, IP, Navn)" required>
                            <input type="text" id="tModule" class="form-control bg-dark text-light border-secondary mb-2" placeholder="Modul ID (ex: 22)" required>
                            <button type="submit" class="btn btn-outline-danger w-100">Affyr Asynkront</button>
                        </form>
                        <div id="triggerResult" class="mt-2 text-warning small"></div>
                    </div>
                    
                    <div class="card p-3 mb-4" style="border-color: #f1c40f;">
                        <h5 class="text-accent" style="color: #f1c40f !important;">📂 Forensic Dropzone</h5>
                        <div id="dropzone" class="dropzone">
                            Træk .PCAP, .EML eller .PDF hertil for auto-analyse
                        </div>
                        <div id="uploadResult" class="mt-2 text-info small"></div>
                    </div>
                    
                    <div class="card p-3 mb-4" style="border-color: #00e5ff;">
                        <h5 class="text-accent">🖥️ Server Terminal Output</h5>
                        <div id="logTerminal" class="p-2" style="background-color: #000; height: 250px; overflow-y: auto; font-family: monospace; color: #00ff00; font-size: 0.75rem; border: 1px solid #3b3b54; border-radius: 4px; white-space: pre-wrap;">
                            Venter på The Production Worker...
                        </div>
                        <a href="/api/v1/download_report/" class="btn btn-outline-success w-100 mt-3">⬇️ Download Master Report</a>
                    </div>
                    <div class="card p-3 mb-4">
                        <h5 class="text-accent">Modul Aktivitet (Top 100)</h5>
                        <canvas id="moduleChart"></canvas>
                    </div>
                </div>
                <div class="col-md-9">
                        <div class="card p-3">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <h5 class="text-accent mb-0">Seneste Efterretninger</h5>
                            <form method="GET" action="/" class="d-flex" style="width: 350px;">
                                <input class="form-control form-control-sm me-2 bg-dark text-light border-secondary" type="search" name="q" placeholder="Deep Search (JSON, Target)..." value="{% if query %}{{ query }}{% endif %}">
                                <button class="btn btn-sm btn-outline-info" type="submit">Søg</button>
                                {% if query %}<a href="/" class="btn btn-sm btn-outline-danger ms-2">X</a>{% endif %}
                            </form>
                        </div>
                            <div class="table-responsive" style="max-height: 500px; overflow-y: auto;">
                                <table class="table table-dark table-hover table-sm align-middle">
                                    <thead style="position: sticky; top: 0; z-index: 1;">
                                        <tr>
                                            <th>ID</th>
                                            <th>Tidspunkt</th>
                                            <th>Modul</th>
                                            <th>Mål</th>
                                            <th>Aktion</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for r in records %}
                                        <tr>
                                            <td><a href="/record/{{ r.id }}/" class="text-info fw-bold" style="text-decoration: none;">#{{ r.id }}</a></td>
                                            <td class="text-muted">{{ r.timestamp|date:"Y-m-d H:i:s" }}</td>
                                            <td><span class="badge" style="background-color: #3b3b54; color: #00e5ff;">{{ r.source_module }}</span></td>
                                            <td class="text-warning fw-bold">{{ r.target }}</td>
                                            <td><button onclick="deleteRecord({{ r.id }})" class="btn btn-sm btn-outline-danger py-0 px-2">X</button></td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                <script>
                    const ctx = document.getElementById('moduleChart').getContext('2d');
                    new Chart(ctx, {
                        type: 'doughnut',
                        data: {
                            labels: [{% for k in stats.keys %}'{{ k }}',{% endfor %}],
                            datasets: [{
                                data: [{% for v in stats.values %}{{ v }},{% endfor %}],
                                backgroundColor: ['#ff007f', '#00e5ff', '#f1c40f', '#2ecc71', '#9b59b6', '#e74c3c'],
                                borderColor: '#1e1e2f',
                                borderWidth: 2
                            }]
                        },
                        options: { plugins: { legend: { position: 'bottom', labels: { color: '#cfd2d9' } } } }
                    });

                document.getElementById('triggerForm')?.addEventListener('submit', function(e) {
                    e.preventDefault();
                    const resDiv = document.getElementById('triggerResult');
                    resDiv.innerHTML = "<i>Sender opgave til Celery-køen...</i>";
                    fetch('/api/v1/trigger/', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            target: document.getElementById('tTarget').value,
                            module_id: document.getElementById('tModule').value
                        })
                    })
                    .then(r => r.json())
                    .then(d => { resDiv.innerHTML = "<b>" + (d.message || d.error) + "</b>"; })
                    .catch(err => { resDiv.innerHTML = "<span class='text-danger'>Fejl: " + err + "</span>"; });
                });

                function deleteRecord(id) {
                    if(confirm('Er du sikker på, at du vil slette Record #' + id + ' for evigt?')) {
                        fetch('/api/v1/record/' + id + '/', { method: 'DELETE' })
                        .then(r => r.json())
                        .then(d => { if(d.status === 'success') location.reload(); else alert('Fejl: ' + d.error); });
                    }
                }

                // Batch 9: Drag and Drop Upload Logic
                const dropzone = document.getElementById('dropzone');
                const uploadResult = document.getElementById('uploadResult');

                dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
                dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
                dropzone.addEventListener('drop', (e) => {
                    e.preventDefault();
                    dropzone.classList.remove('dragover');
                    if(e.dataTransfer.files.length > 0) {
                        const file = e.dataTransfer.files[0];
                        uploadResult.innerHTML = `<i>Uploader ${file.name}...</i>`;
                        
                        const formData = new FormData();
                        formData.append('file', file);
                        
                        fetch('/api/v1/upload/', { method: 'POST', body: formData })
                        .then(r => r.json())
                        .then(d => {
                            uploadResult.innerHTML = "<b>" + (d.message || d.error) + "</b>";
                        })
                        .catch(err => { uploadResult.innerHTML = "<span class='text-danger'>Fejl: " + err + "</span>"; });
                    }
                });

                // Batch 7: Live Terminal Auto-Scroller
                setInterval(function() {
                    fetch('/api/v1/logs/')
                    .then(r => r.text())
                    .then(text => {
                        const term = document.getElementById('logTerminal');
                        const isScrolledToBottom = term.scrollHeight - term.clientHeight <= term.scrollTop + 50;
                        term.textContent = text;
                        if(isScrolledToBottom) term.scrollTop = term.scrollHeight;
                    });
                }, 2000);
                </script>
            {% endif %}
        </div>
    </body>
    </html>
    """
    engine = Engine(app_dirs=False)
    template = engine.from_string(html_template)
    context = Context({"records": records, "stats": stats, "error_msg": error_msg, "query": query})
    return HttpResponse(template.render(context))

def record_detail(request, record_id):
    """Dedikeret visning for rå JSON data."""
    try:
        record = OsintRecord.objects.get(id=record_id)
        try:
            parsed_json = json.loads(record.data_json)
            pretty_json = json.dumps(parsed_json, indent=4, ensure_ascii=False)
        except:
            pretty_json = record.data_json

        html_template = """
        <!DOCTYPE html>
        <html lang="da" data-bs-theme="dark">
        <head>
            <meta charset="UTF-8">
            <title>Record #{{ record.id }} // GOLIATH</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { background-color: #0b0b10; color: #cfd2d9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
                .navbar { background-color: #1e1e2f !important; border-bottom: 2px solid #ff007f; }
                .json-block { background-color: #12121c; border: 1px solid #3b3b54; padding: 20px; border-radius: 5px; overflow-x: auto; color: #00e5ff; font-family: monospace; }
            </style>
        </head>
        <body>
            <nav class="navbar navbar-dark mb-4 p-3">
                <div class="container-fluid">
                    <span class="navbar-brand text-danger fw-bold">🦅 GOLIATH DATA INSPECTOR</span>
                    <a href="/" class="btn btn-outline-info btn-sm">Tilbage til Dashboard</a>
                </div>
            </nav>
            <div class="container">
                <h4 class="text-warning">Record ID: {{ record.id }} | Mål: {{ record.target }}</h4>
                <p class="text-muted">Modul: <span class="badge bg-secondary">{{ record.source_module }}</span> | Timestamp: {{ record.timestamp }}</p>
                <div class="json-block"><pre><code>{{ pretty_json }}</code></pre></div>
            </div>
        </body>
        </html>
        """
        engine = Engine(app_dirs=False)
        template = engine.from_string(html_template)
        context = Context({"record": record, "pretty_json": pretty_json})
        return HttpResponse(template.render(context))
    except Exception as e:
        return HttpResponse(f"Record not found or error: {e}", status=404)

def network_graph(request):
    """GOLIATH V46: Live Vis.js Relational Graph Engine."""
    nodes_dict = {}
    edges = []
    
    def add_node(n_id, group):
        clean_id = str(n_id).strip()
        if clean_id and clean_id not in nodes_dict:
            nodes_dict[clean_id] = {"id": clean_id, "label": clean_id, "group": group}
            
    records = OsintRecord.objects.all()
    for r in records:
        try:
            data = json.loads(r.data_json)
            target = r.target.strip()
            add_node(target, "Target")
            
            # Udvinder OSINT spor og linker dem til Målet
            mapping = [
                ("Fundne_Emails", "Email"), ("Telefonnumre", "Phone"),
                ("IP_Adresser", "IP"), ("Domæner", "Domain"),
                ("Fundne_Brugernavne", "Alias"), ("Identificerede_Aliaser", "Alias"),
                ("Kryptovaluta_Wallets", "Crypto")
            ]
            
            for key, group in mapping:
                items = data.get(key, [])
                if isinstance(items, dict): items = items.keys() # Håndterer Titan/Sniper dicts
                for item in items:
                    if isinstance(item, str):
                        add_node(item, group)
                        edges.append({"from": target, "to": item.strip(), "label": "Tilknyttet"})
        except: pass
        
    graph_data = json.dumps({"nodes": list(nodes_dict.values()), "edges": edges})
    
    html_template = """
    <!DOCTYPE html>
    <html lang="da" data-bs-theme="dark">
    <head>
        <meta charset="UTF-8">
        <title>NEXUS GRAPH // COMMAND CENTER</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <style>
            body { background-color: #0b0b10; color: #cfd2d9; font-family: sans-serif; margin: 0; }
            .navbar { background-color: #1e1e2f !important; border-bottom: 2px solid #00e5ff; }
            #network-map { width: 100vw; height: calc(100vh - 56px); background-color: #0b0b10; }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-dark p-2">
            <div class="container-fluid">
                <span class="navbar-brand text-info fw-bold">🌐 NEXUS INTELLIGENCE GRAPH</span>
                <a href="/" class="btn btn-outline-danger btn-sm">Tilbage til Dashboard</a>
            </div>
        </nav>
        <div id="network-map"></div>
        <script type="text/javascript">
            var graphData = {{ graph_data|safe }};
            var container = document.getElementById('network-map');
            var data = { nodes: new vis.DataSet(graphData.nodes), edges: new vis.DataSet(graphData.edges) };
            var options = {
                nodes: { shape: 'dot', size: 16, font: { color: '#cfd2d9', size: 12 }, borderWidth: 2 },
                edges: { font: { color: '#a5b1c2', size: 10, align: 'middle' }, arrows: 'to', color: '#3b3b54' },
                physics: { stabilization: true, barnesHut: { gravitationalConstant: -3000, springLength: 150 } },
                groups: {
                    Target: { color: { background: '#ff007f', border: '#fff' }, size: 25 },
                    Email: { color: { background: '#00e5ff', border: '#fff' } },
                    Phone: { color: { background: '#2ecc71', border: '#fff' } },
                    Alias: { color: { background: '#f1c40f', border: '#fff' } },
                    Crypto: { color: { background: '#9b59b6', border: '#fff' } }
                }
            };
            var network = new vis.Network(container, data, options);
        </script>
    </body>
    </html>
    """
    return HttpResponse(Engine(app_dirs=False).from_string(html_template).render(Context({"graph_data": graph_data})))

@csrf_exempt
def trigger_scan(request):
    """API Endpoint: Modtager opgaver fra web og sender til Celery eller Tråd."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            target = data.get('target')
            module_id = data.get('module_id', 'auto')
            
            if celery_app:
                try:
                    celery_app.send_task("execute_goliath_module", args=[module_id, target])
                    return JsonResponse({"status": "success", "message": f"Celery Task i kø for {target}!"})
                except Exception: pass
            
            # Fallback til baggrundstråd (Zero-Crash OPSEC)
            threading.Thread(target=lambda: subprocess.run([sys.executable, "main.py", "-t", target, "-m", str(module_id)]), daemon=True).start()
            return JsonResponse({"status": "success", "message": f"Fallback: Tråd startet direkte for {target}!"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method Not Allowed"}, status=405)

@csrf_exempt
def delete_record(request, record_id):
    """API Endpoint: Sletter en OSINT record permanent."""
    if request.method == 'DELETE':
        try:
            record = OsintRecord.objects.get(id=record_id)
            target_name = record.target
            record.delete()
            
            # Deep Eradication: Sletter også de fysiske bevisfiler
            from core.utils import sanitize_filename
            loot_dir = session.get("loot_folder", "workspaces/standard_sag")
            safe_target = sanitize_filename(target_name)
            
            for f in glob.glob(os.path.join(loot_dir, f"*{safe_target}*.json")):
                try: os.remove(f)
                except: pass
                
            return JsonResponse({"status": "success", "message": "Record og fysiske beviser slettet for evigt."})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def handle_upload(request):
    """API Endpoint: Modtager filer og dirigerer dem til de korrekte OSINT moduler (Batch 9)."""
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            uploaded_file = request.FILES['file']
            filename = uploaded_file.name.lower()
            
            # Sikker lagring
            loot_dir = session.get("loot_folder", "workspaces/standard_sag")
            upload_dir = os.path.join(loot_dir, "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            
            fs = FileSystemStorage(location=upload_dir)
            saved_name = fs.save(uploaded_file.name, uploaded_file)
            file_path = os.path.abspath(os.path.join(upload_dir, saved_name))
            
            # Modul Routing baseret på filtype
            target_module = "07" # Standard: Send til TITAN Forensics (Billeder, zip, docx, pdf)
            if filename.endswith(('.pcap', '.pcapng', '.eml')):
                target_module = "06" # Send PCAP og Mails til InfraTracker
                
            if celery_app:
                try:
                    celery_app.send_task("execute_goliath_module", args=[target_module, file_path])
                    return JsonResponse({"status": "success", "message": f"{saved_name} sendt til Modul {target_module}!"})
                except Exception: pass
            
            return JsonResponse({"error": "Celery er offline. Kør The Worker for at analysere filer."}, status=503)
            
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Ingen fil modtaget"}, status=400)

def get_logs(request):
    """Henter de seneste 50 linjer fra Celery worker-loggen (Batch 7)."""
    log_path = "logs/celery_worker.log"
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-50:]
            return HttpResponse("".join(lines), content_type='text/plain')
    except Exception:
        return HttpResponse("Initialiserer log-fil. Sørg for at køre goliath_worker.py i baggrunden...", content_type='text/plain')

def download_report(request):
    """Downloader den nyeste GOLIATH MASTER REPORT (Batch 7)."""
    loot_dir = session.get("loot_folder", "workspaces/standard_sag")
    reports = glob.glob(os.path.join(loot_dir, "GOLIATH_MASTER_REPORT_*.html"))
    if reports:
        latest = max(reports, key=os.path.getctime)
        with open(latest, 'r', encoding='utf-8') as f:
            response = HttpResponse(f.read(), content_type='text/html')
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(latest)}"'
            return response
    return JsonResponse({"error": "Ingen rapport fundet. Kør 'report' i terminalen først for at generere den."})

def api_datalake(request):
    """Opgraderet API Endpoint: Bruger nu Django ORM i stedet for rå SQLite."""
    try:
        records = OsintRecord.objects.all().order_by('-id')[:50]
        data = [{"id": r.id, "timestamp": r.timestamp.isoformat(), "module": r.source_module, "target": r.target} for r in records]
        return JsonResponse({"status": "GOLIATH WEB CORE ONLINE", "records": data})
    except Exception as e:
        return JsonResponse({"error": str(e), "status": "offline"})

# =====================================================================
# 4. URL ROUTING & EXECUTION
# =====================================================================
urlpatterns = [
    path('', dashboard),
    path('record/<int:record_id>/', record_detail),
    path('graph/', network_graph),
    path('api/v1/trigger/', trigger_scan),
    path('api/v1/record/<int:record_id>/', delete_record),
    path('api/v1/upload/', handle_upload),
    path('api/v1/loot/', api_datalake),
    path('api/v1/logs/', get_logs),
    path('api/v1/download_report/', download_report),
]

def run_server(port="8000"):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', int(port))) == 0:
                print(f"\n{C.YELLOW}[!] Port {port} er allerede i brug. Web serveren kører muligvis allerede!{C.RESET}")
                return
        execute_from_command_line(['manage.py', 'runserver', f'0.0.0.0:{port}', '--noreload'])
    except Exception as e:
        print(f"\n{C.RED}[!] KRITISK NEDBRUD I WEB CORE: {e}{C.RESET}")

class GoliathWebServer:
    @staticmethod
    def start_background():
        import sys
        import os
        # GOLIATH V46: Process Isolation og Telemetry Routing.
        os.makedirs("logs", exist_ok=True)
        log_file = open("logs/web_server_error.log", "a")
        subprocess.Popen(
            [sys.executable, os.path.abspath(__file__)],
            stdout=log_file,
            stderr=subprocess.STDOUT
        )

if __name__ == "__main__":
    run_server()
