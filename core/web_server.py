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

from pathlib import Path
def ensure_venv():
    """GOLIATH AUTO-HEAL: Tvinger webserveren ind i Venv for at forhindre ModuleNotFound."""
    if sys.prefix == sys.base_prefix:
        venv_python = Path(BASE_DIR) / "venv" / "bin" / "python"
        if venv_python.exists():
            os.execv(str(venv_python), [str(venv_python)] + sys.argv)
        else:
            print("\033[91m[!] Intet 'venv' fundet. Kør './goliath.sh' først.\033[0m")
            sys.exit(1)
ensure_venv()

import json
import subprocess
import threading
import glob
import socket
import django
from django.conf import settings
from django.core.management import call_command
try:
    import websockets
    import asyncio
except ImportError:
    websockets = None
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
        INSTALLED_APPS=[
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'core'
        ],
        MIDDLEWARE=[
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ],
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': True,
        }],
        LOGIN_URL='/login/',
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
        
class ScheduledHunt(models.Model):
    """GOLIATH V46: Relationel model inspireret af Reprohack til at håndtere Cronjobs."""
    id = models.AutoField(primary_key=True)
    target = models.CharField(max_length=255)
    module_id = models.CharField(max_length=50)
    interval_minutes = models.IntegerField(default=60)
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'scheduled_hunts'
        app_label = 'core'

class ActiveOperation(models.Model):
    """GOLIATH V47: Live tracking af Celery / Background tasks."""
    task_id = models.CharField(max_length=255, primary_key=True)
    module_id = models.CharField(max_length=50)
    target = models.CharField(max_length=255)
    status = models.CharField(max_length=50, default="Processing")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'active_operations'
        app_label = 'core'

class ExtractedEmail(models.Model):
    """GOLIATH V48: Entity Extraction Model for hurtig søgning."""
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()
    source_module = models.CharField(max_length=255)
    target = models.CharField(max_length=255)
    email = models.CharField(max_length=255)

    class Meta:
        db_table = 'extracted_emails'
        managed = False
        app_label = 'core'

class ExtractedCredential(models.Model):
    """GOLIATH V48: Entity Extraction Model for hurtig søgning af lækager."""
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()
    source_module = models.CharField(max_length=255)
    target = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)

    class Meta:
        db_table = 'extracted_credentials'
        managed = False
        app_label = 'core'

class ExtractedApi(models.Model):
    """GOLIATH V49: Entity Model for fundne SPA Backend-Endpoints."""
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()
    source_module = models.CharField(max_length=255)
    target = models.CharField(max_length=255)
    endpoint = models.CharField(max_length=1000)
    method = models.CharField(max_length=50)

    class Meta:
        db_table = 'extracted_apis'
        managed = False
        app_label = 'core'

class HarvestedData(models.Model):
    """GOLIATH V50: Model for mass-harvested JSON payloads fra API'er."""
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()
    source_module = models.CharField(max_length=255)
    target = models.CharField(max_length=255)
    endpoint = models.CharField(max_length=1000)
    payload = models.TextField()

    class Meta:
        db_table = 'harvested_data'
        managed = False
        app_label = 'core'

class MasterPersona(models.Model):
    """GOLIATH V51: 360-Graders Profil Container."""
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()
    target = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)
    social_handle = models.CharField(max_length=255)
    raw_data_ref = models.TextField()
    last_ip = models.CharField(max_length=50, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    confidence_score = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)

    class Meta:
        db_table = 'master_personas'
        managed = False
        app_label = 'core'

class WatchlistItem(models.Model):
    """GOLIATH V53: Mål til proaktiv overvågning."""
    id = models.AutoField(primary_key=True)
    keyword = models.CharField(max_length=255)
    type = models.CharField(max_length=50, default="Generic")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'watchlist'
        managed = False
        app_label = 'core'

class SecurityAlert(models.Model):
    """GOLIATH V53: Persistente HVT alarmer."""
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()
    source_module = models.CharField(max_length=255)
    target = models.CharField(max_length=255)
    keyword = models.CharField(max_length=255)
    snippet = models.TextField()
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'security_alerts'
        managed = False
        app_label = 'core'

class PersonaReview(models.Model):
    """GOLIATH V56: Operatør-vurdering inspireret af Reprohack Reviews."""
    id = models.AutoField(primary_key=True)
    persona_id = models.IntegerField()
    operator_name = models.CharField(max_length=255)
    comment = models.TextField()
    rating = models.IntegerField() # 1-5 stjerner
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'persona_reviews'
        managed = False
        app_label = 'core'

# Sikrer at tabellerne eksisterer uden at køre 'makemigrations' for OPSEC reasons
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('''CREATE TABLE IF NOT EXISTS osint_records (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, source_module TEXT, target TEXT, data_json TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS scheduled_hunts (id INTEGER PRIMARY KEY AUTOINCREMENT, target TEXT, module_id TEXT, interval_minutes INTEGER, is_active BOOLEAN, last_run DATETIME, created_at DATETIME)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS active_operations (task_id TEXT PRIMARY KEY, module_id TEXT, target TEXT, status TEXT, created_at DATETIME)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS extracted_emails (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, source_module TEXT, target TEXT, email TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS extracted_credentials (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, source_module TEXT, target TEXT, username TEXT, password TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS extracted_apis (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, source_module TEXT, target TEXT, endpoint TEXT, method TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS harvested_data (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, source_module TEXT, target TEXT, endpoint TEXT, payload TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS master_personas (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, target TEXT, name TEXT, email TEXT, phone TEXT, social_handle TEXT, raw_data_ref TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS watchlist (id INTEGER PRIMARY KEY AUTOINCREMENT, keyword TEXT, type TEXT, added_at DATETIME)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS security_alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, source_module TEXT, target TEXT, keyword TEXT, snippet TEXT, is_read BOOLEAN DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS persona_reviews (id INTEGER PRIMARY KEY AUTOINCREMENT, persona_id INTEGER, operator_name TEXT, comment TEXT, rating INTEGER, timestamp DATETIME)''')

# Auto-initialiserer RBAC Auth tabeller og opretter Master Admin
try:
    call_command('migrate', interactive=False, verbosity=0)
    from django.contrib.auth.models import User
    if not User.objects.filter(username='goliath_admin').exists():
        User.objects.create_superuser('goliath_admin', 'admin@goliath.local', 'GoliathApex2026!')
        print(f"\033[92m[+] Master Admin Oprettet: goliath_admin / GoliathApex2026!\033[0m")
except Exception as e:
    print(f"Migration / Auth Error: {e}")

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
        from django.utils import timezone
        from celery import current_task
        task_id = current_task.request.id if current_task else "unknown"
        
        if task_id != "unknown":
            try:
                ActiveOperation.objects.update_or_create(
                    task_id=task_id,
                    defaults={'module_id': str(module_id), 'target': target, 'status': 'Processing', 'created_at': timezone.now()}
                )
            except Exception: pass
            
        subprocess.run([sys.executable, "main.py", "-t", target, "-m", str(module_id)])
        
        if task_id != "unknown":
            try:
                op = ActiveOperation.objects.get(task_id=task_id)
                op.status = "Success"
                op.save()
            except Exception: pass
            
        return f"Modul {module_id} mod {target} fuldført."
        
    @celery_app.task(name="goliath_worker.execute_goliath_module")
    def execute_goliath_module_legacy(module_id, target):
        """Ghost-Task Catcher: Opfanger beskeder fra ældre batches og kører dem fejlfrit."""
        return execute_goliath_module(module_id, target)
        
    @celery_app.task(name="goliath_cron_scheduler")
    def goliath_cron_scheduler():
        """Kører hvert minut og tjekker om en ScheduledHunt skal affyres (Continuous Monitoring)."""
        from django.utils import timezone
        from datetime import timedelta
        hunts = ScheduledHunt.objects.filter(is_active=True)
        now = timezone.now()
        for hunt in hunts:
            if not hunt.last_run or now >= (hunt.last_run + timedelta(minutes=hunt.interval_minutes)):
                print(f"[CRON] Affyrer automatisk {hunt.module_id} mod {hunt.target}")
                celery_app.send_task("execute_goliath_module", args=[hunt.module_id, hunt.target])
                hunt.last_run = now
                hunt.save()
                
    # Reprohack-style Celery Beat konfiguration
    celery_app.conf.beat_schedule = {'run-scheduler-every-minute': {'task': 'goliath_cron_scheduler', 'schedule': 60.0}}
    celery_app.conf.timezone = 'UTC'
except ImportError:
    celery_app = None

# =====================================================================
# 3. VIEWS & TEMPLATES (HTML DASHBOARD)
# =====================================================================
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect

@csrf_exempt
def login_view(request):
    """GOLIATH V46: Secure Login Portal (RBAC)"""
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect('/')
        return HttpResponse("<script>alert('Afgang Nægtet. Uautoriseret.'); window.location='/login/';</script>", status=401)
    
    html = """
    <!DOCTYPE html><html data-bs-theme="dark"><head><title>GOLIATH // AUTH</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet"></head>
    <body class="bg-dark text-light d-flex align-items-center justify-content-center vh-100" style="background-color:#0b0b10 !important;">
    <div class="card p-5 border-danger" style="width: 400px; background-color:#1e1e2f; box-shadow: 0 0 20px rgba(255,0,127,0.2);">
        <h3 class="text-danger fw-bold mb-4 text-center">🦅 GOLIATH ACCESS</h3>
        <form method="POST">
            <input class="form-control mb-3 bg-dark text-light border-secondary" name="username" placeholder="Brugernavn" required>
            <input type="password" class="form-control mb-4 bg-dark text-light border-secondary" name="password" placeholder="Adgangskode" required>
            <button class="btn btn-outline-danger w-100 fw-bold" type="submit">INITIER SESSION</button>
        </form>
    </div></body></html>
    """
    return HttpResponse(html)

def logout_view(request):
    logout(request)
    return redirect('/login/')

@login_required
def dashboard(request):
    """Interaktivt HTML Dashboard med Chart.js og Bootstrap (Dark Mode)."""
    error_msg = None
    records = []
    stats = {}
    scheduled_hunts = []
    active_operations = []
    watchlist_items = []
    security_alerts = []
    master_personas = []
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
            
        # Hent aktive overvågninger
        scheduled_hunts = ScheduledHunt.objects.filter(is_active=True).order_by('-created_at')
        active_operations = ActiveOperation.objects.all().order_by('-created_at')[:10]
        watchlist_items = WatchlistItem.objects.all().order_by('-added_at')
        security_alerts = SecurityAlert.objects.filter(is_read=False).order_by('-timestamp')[:20]
        master_personas = MasterPersona.objects.all().order_by('-confidence_score')[:20]
        
        # Hent Entities
        if query:
            emails_qs = ExtractedEmail.objects.filter(email__icontains=query).order_by('-id')[:50]
            creds_qs = ExtractedCredential.objects.filter(models.Q(username__icontains=query) | models.Q(password__icontains=query)).order_by('-id')[:50]
        else:
            emails_qs = ExtractedEmail.objects.all().order_by('-id')[:25]
            creds_qs = ExtractedCredential.objects.all().order_by('-id')[:25]
            
        # GOLIATH V49: Entity Aggregation for Charts
        cred_stats_qs = ExtractedCredential.objects.values('source_module').annotate(count=models.Count('id')).order_by('-count')[:10]
        cred_stats = {x['source_module']: x['count'] for x in cred_stats_qs}
        
        email_stats_qs = ExtractedEmail.objects.values('source_module').annotate(count=models.Count('id')).order_by('-count')[:10]
        email_stats = {x['source_module']: x['count'] for x in email_stats_qs}
    except Exception as e:
        error_msg = f"Data Lake er tom eller ikke initialiseret. Kør et modul i terminalen først! (Detaljer: {e})"
        emails_qs = []
        creds_qs = []
        cred_stats = {}
        email_stats = {}
        master_personas = []

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
                <span class="navbar-text ms-4 text-warning fw-bold">👤 {{ request.user.username|upper }}</span>
                <a href="/logout/" class="btn btn-outline-danger btn-sm ms-3">Afslut Session</a>
                <a href="/graph/" class="btn btn-outline-info btn-sm ms-auto">🌐 Visualisér Intelligence Netværk</a>
            </div>
        </nav>
        
        <!-- GOLIATH V53 TOAST CONTAINER -->
        <div class="toast-container position-fixed top-0 end-0 p-3" style="z-index: 10000;" id="toastContainer"></div>
        
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
                    
                    <div class="card p-3 mb-4" style="border-color: #9b59b6;">
                        <h5 class="text-accent" style="color: #9b59b6 !important;">⏳ Continuous Monitoring</h5>
                        <form id="scheduleForm">
                            <input type="text" id="sTarget" class="form-control bg-dark text-light border-secondary mb-2" placeholder="Target" required>
                            <input type="text" id="sModule" class="form-control bg-dark text-light border-secondary mb-2" placeholder="Modul ID (ex: 36)" required>
                            <input type="number" id="sInterval" class="form-control bg-dark text-light border-secondary mb-2" placeholder="Interval (minutter)" value="60" required>
                            <button type="submit" class="btn btn-outline-primary w-100" style="color: #9b59b6; border-color: #9b59b6;">Start Overvågning</button>
                        </form>
                        <div id="scheduleResult" class="mt-2 text-info small"></div>
                    </div>
                    
                    <div class="card p-3 mb-4" style="border-color: #e74c3c;">
                        <h5 class="text-accent" style="color: #e74c3c !important;">🎯 HVT Watchlist</h5>
                        <form id="watchlistForm">
                            <input type="text" id="wKeyword" class="form-control bg-dark text-light border-secondary mb-2" placeholder="Keyword/Email/Navn" required>
                            <button type="submit" class="btn btn-outline-danger w-100">Tilføj til Watchlist</button>
                        </form>
                        <div class="mt-3">
                            <ul class="list-group list-group-flush" style="max-height: 150px; overflow-y: auto;">
                                {% for w in watchlist_items %}
                                <li class="list-group-item bg-dark text-light border-secondary d-flex justify-content-between align-items-center py-1 px-2" style="font-size: 0.85rem;">
                                    {{ w.keyword }}
                                    <button onclick="removeWatchlist({{ w.id }})" class="btn btn-sm btn-link text-danger p-0 m-0 text-decoration-none">X</button>
                                </li>
                                {% endfor %}
                            </ul>
                        </div>
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
                        <a href="/api/v1/download_verified/" class="btn btn-success w-100 mt-2 fw-bold" style="background-color: #2ecc71; color: black; border: none;">🛡️ Download Verificeret Dossier</a>
                        <a href="/api/v1/download_export/" class="btn btn-outline-warning w-100 mt-2">🔐 Download AES Export (.aes)</a>
                    </div>
                    <div class="card p-3 mb-4">
                        <h5 class="text-accent">Modul Aktivitet (Top 100)</h5>
                        <canvas id="moduleChart"></canvas>
                    </div>
                </div>
                <div class="col-md-9">
                    
                    {% if security_alerts %}
                    <div class="alert alert-danger mb-4" style="background-color: #2c0b14; border: 1px solid #ff007f;">
                        <h5 class="alert-heading text-danger fw-bold">🚨 HIGH VALUE TARGET ALERTS (Ubehandlede)</h5>
                        <ul class="mb-0">
                            {% for alert in security_alerts %}
                            <li>
                                <strong>{{ alert.timestamp|date:"H:i:s" }}</strong> - Mål fundet: <span class="text-warning">{{ alert.keyword }}</span> 
                                (Opsnappet af <em>{{ alert.source_module }}</em> mod <em>{{ alert.target }}</em>)
                                <button onclick="markAlertRead({{ alert.id }})" class="btn btn-sm btn-link text-info">Markér læst</button>
                            </li>
                            {% endfor %}
                        </ul>
                    </div>
                    {% endif %}
                    
                    <!-- GOLIATH V56: Master Personas Intelligence UI -->
                    <div class="card p-3 mb-4" style="border-color: #9b59b6;">
                        <h5 class="text-accent mb-3" style="color: #9b59b6 !important;">👥 Master Personas (Intelligence Profiles)</h5>
                        <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
                            <table class="table table-dark table-sm align-middle">
                                <thead style="position: sticky; top: 0; z-index: 1; background: #12121c;">
                                    <tr><th>Target / Navn</th><th>Kontakt</th><th>Confidence Score</th><th>Status</th><th>Aktion</th></tr>
                                </thead>
                                <tbody>
                                    {% for p in master_personas %}
                                    <tr>
                                        <td><strong class="text-info">{{ p.name|default:"Ukendt" }}</strong><br><span class="text-muted small">{{ p.target }}</span></td>
                                        <td><span class="text-warning">{{ p.email|default:"N/A" }}</span><br><span class="text-success">{{ p.phone|default:"N/A" }}</span></td>
                                        <td style="width: 25%;">
                                            <div class="d-flex align-items-center">
                                                <span class="me-2 small fw-bold">{{ p.confidence_score }}%</span>
                                                <div class="progress w-100" style="height: 8px; background-color: #2c2c3e;">
                                                    <div class="progress-bar {% if p.confidence_score >= 70 %}bg-success{% elif p.confidence_score >= 40 %}bg-warning{% else %}bg-danger{% endif %}" role="progressbar" style="width: {{ p.confidence_score }}%;"></div>
                                                </div>
                                            </div>
                                        </td>
                                        <td>
                                            {% if p.is_verified %}
                                                <span class="badge bg-success">Verificeret</span>
                                            {% else %}
                                                <span class="badge bg-danger">Afventer Review</span>
                                            {% endif %}
                                        </td>
                                        <td>
                                            {% if not p.is_verified %}
                                                <button onclick="verifyPersona({{ p.id }})" class="btn btn-sm btn-outline-info py-0 px-2">Godkend</button>
                                            {% endif %}
                                            <button onclick="viewPersona({{ p.id }})" class="btn btn-sm btn-outline-secondary py-0 px-2">Vis</button>
                                        </td>
                                    </tr>
                                    {% empty %}
                                    <tr><td colspan="5" class="text-center text-muted">Ingen profil-data at vise. Kør Modul 27 først.</td></tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div class="card p-3 mb-4" style="border-color: #00e5ff;">
                        <h5 class="text-accent mb-3">📡 Live Operationer (Celery/Threads)</h5>
                        <table class="table table-dark table-sm align-middle">
                            <thead><tr><th>Task ID</th><th>Mål</th><th>Modul</th><th>Status</th></tr></thead>
                            <tbody>
                                {% for op in active_operations %}
                                <tr>
                                    <td><span class="text-muted" style="font-size: 0.8rem;">{{ op.task_id|slice:":8" }}</span></td>
                                    <td class="text-warning fw-bold">{{ op.target }}</td>
                                    <td>{{ op.module_id }}</td>
                                    <td>
                                        {% if op.status == 'Processing' %}
                                            <span class="badge bg-warning text-dark"><span class="spinner-border spinner-border-sm" style="width: 10px; height: 10px;"></span> Processing</span>
                                        {% elif op.status == 'Success' %}
                                            <span class="badge bg-success">Success</span>
                                        {% else %}
                                            <span class="badge bg-danger">Failed</span>
                                        {% endif %}
                                    </td>
                                </tr>
                                {% endfor %}
                                {% if not active_operations %}
                                <tr><td colspan="4" class="text-center text-muted">Ingen aktive operationer pt.</td></tr>
                                {% endif %}
                            </tbody>
                        </table>
                    </div>

                        <div class="card p-3 mb-4">
                            <h5 class="text-accent mb-3" style="color: #9b59b6 !important;">Aktive Cronjobs (Automatiserede Scans)</h5>
                            <table class="table table-dark table-sm align-middle">
                                <thead><tr><th>ID</th><th>Mål</th><th>Modul</th><th>Interval</th><th>Sidst Kørt</th><th>Aktion</th></tr></thead>
                                <tbody>
                                    {% for h in scheduled_hunts %}
                                    <tr>
                                        <td>#{{ h.id }}</td>
                                        <td class="text-warning fw-bold">{{ h.target }}</td>
                                        <td>{{ h.module_id }}</td>
                                        <td>{{ h.interval_minutes }} min</td>
                                        <td class="text-muted">{{ h.last_run|default:"Aldrig" }}</td>
                                        <td><button onclick="stopHunt({{ h.id }})" class="btn btn-sm btn-outline-danger py-0 px-2">Stop</button></td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>

                        <!-- GOLIATH V49: Entity Analytics Graphs -->
                        <div class="row mb-4">
                            <div class="col-md-6">
                                <div class="card p-3 h-100" style="border-color: #ff007f;">
                                    <h6 class="text-accent mb-2" style="color: #ff007f !important;">🔥 Top Kilder: Passwords</h6>
                                    <canvas id="credChart" height="150"></canvas>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card p-3 h-100" style="border-color: #00e5ff;">
                                    <h6 class="text-accent mb-2" style="color: #00e5ff !important;">📧 Top Kilder: Emails</h6>
                                    <canvas id="emailChart" height="150"></canvas>
                                </div>
                            </div>
                        </div>

                        <!-- GOLIATH V48: Entity Extraction UI -->
                        <div class="row mb-4">
                            <div class="col-md-6">
                                <div class="card p-3 h-100" style="border-color: #ff007f;">
                                    <h5 class="text-accent mb-3" style="color: #ff007f !important;">🚨 Eksponerede Credentials</h5>
                                    <div class="table-responsive" style="max-height: 250px;">
                                        <table class="table table-dark table-sm align-middle">
                                            <thead style="position: sticky; top: 0; z-index: 1; background: #12121c;"><tr><th>Mål/Bruger</th><th>Password</th><th>Kilde</th></tr></thead>
                                            <tbody>
                                                {% for c in credentials %}
                                                <tr>
                                                    <td class="text-warning">{{ c.username }}</td>
                                                    <td class="text-danger fw-bold" style="font-family: monospace;">{{ c.password }}</td>
                                                    <td><span class="badge bg-secondary">{{ c.source_module }}</span></td>
                                                </tr>
                                                {% empty %}
                                                <tr><td colspan="3" class="text-muted text-center">Ingen credentials fundet.</td></tr>
                                                {% endfor %}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card p-3 h-100" style="border-color: #00e5ff;">
                                    <h5 class="text-accent mb-3">📧 Udtrukne Emails</h5>
                                    <div class="table-responsive" style="max-height: 250px;">
                                        <table class="table table-dark table-sm align-middle">
                                            <thead style="position: sticky; top: 0; z-index: 1; background: #12121c;"><tr><th>Email</th><th>Target</th><th>Kilde</th></tr></thead>
                                            <tbody>
                                                {% for e in emails %}
                                                <tr>
                                                    <td class="text-info fw-bold">{{ e.email }}</td>
                                                    <td class="text-muted">{{ e.target }}</td>
                                                    <td><span class="badge bg-secondary">{{ e.source_module }}</span></td>
                                                </tr>
                                                {% empty %}
                                                <tr><td colspan="3" class="text-muted text-center">Ingen emails fundet.</td></tr>
                                                {% endfor %}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>

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

                    // Batch V49: Credential Analytics
                    new Chart(document.getElementById('credChart').getContext('2d'), {
                        type: 'bar',
                        data: {
                            labels: [{% for k in cred_stats.keys %}'{{ k|truncatechars:15 }}',{% endfor %}],
                            datasets: [{
                                label: 'Lækkede Passwords',
                                data: [{% for v in cred_stats.values %}{{ v }},{% endfor %}],
                                backgroundColor: '#ff007f', borderColor: '#1e1e2f', borderWidth: 1
                            }]
                        },
                        options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#cfd2d9' } }, x: { ticks: { color: '#cfd2d9' } } } }
                    });

                    new Chart(document.getElementById('emailChart').getContext('2d'), {
                        type: 'bar',
                        data: {
                            labels: [{% for k in email_stats.keys %}'{{ k|truncatechars:15 }}',{% endfor %}],
                            datasets: [{
                                label: 'Eksponerede Emails',
                                data: [{% for v in email_stats.values %}{{ v }},{% endfor %}],
                                backgroundColor: '#00e5ff', borderColor: '#1e1e2f', borderWidth: 1
                            }]
                        },
                        options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#cfd2d9' } }, x: { ticks: { color: '#cfd2d9' } } } }
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

                document.getElementById('scheduleForm')?.addEventListener('submit', function(e) {
                    e.preventDefault();
                    fetch('/api/v1/schedule/', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            target: document.getElementById('sTarget').value,
                            module_id: document.getElementById('sModule').value,
                            interval_minutes: document.getElementById('sInterval').value
                        })
                    }).then(r => r.json()).then(d => { location.reload(); });
                });
                
                function stopHunt(id) {
                    if(confirm('Stop automatisk overvågning?')) {
                        fetch('/api/v1/schedule/' + id + '/', { method: 'DELETE' })
                        .then(r => r.json()).then(d => location.reload());
                    }
                }

                document.getElementById('watchlistForm')?.addEventListener('submit', function(e) {
                    e.preventDefault();
                    fetch('/api/v1/watchlist/', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ keyword: document.getElementById('wKeyword').value })
                    }).then(r => r.json()).then(d => location.reload());
                });
                
                function removeWatchlist(id) {
                    fetch('/api/v1/watchlist/' + id + '/', { method: 'DELETE' })
                    .then(r => r.json()).then(d => location.reload());
                }
                
                function markAlertRead(id) {
                    fetch('/api/v1/alerts/' + id + '/', { method: 'POST' })
                    .then(r => r.json()).then(d => location.reload());
                }
                
                function verifyPersona(id) {
                    const comment = prompt("Indtast operatør-kommentar (peer-review) for denne verifikation:");
                    if (comment !== null) {
                        fetch('/api/v1/intelligence/verify/' + id + '/', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({ comment: comment, rating: 5 })
                        }).then(r => r.json()).then(d => {
                            if (d.status === 'success') location.reload();
                            else alert('Fejl: ' + d.error);
                        });
                    }
                }
                
                function viewPersona(id) {
                    fetch('/api/v1/intelligence/persona/' + id + '/')
                    .then(r => r.json())
                    .then(d => {
                        if(d.status === 'success') {
                            alert('🕵️ PERSONA PROFIL:\\n\\nNavn: ' + d.persona.name + '\\nEmail: ' + d.persona.email + '\\nTelefon: ' + d.persona.phone + '\\nAlias: ' + d.persona.social_handle + '\\nConfidence: ' + d.persona.confidence_score + '%');
                        }
                    });
                }

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

                // Batch 09: ÆGTE ASYNKRONE WEBSOCKETS (Live Terminal)
                const term = document.getElementById('logTerminal');
                const ws = new WebSocket('ws://' + window.location.hostname + ':8001');
                ws.onopen = function() { term.textContent = "[*] WEBSOCKET FORBUNDET. Venter på The Worker...\\n"; };
                ws.onmessage = function(event) {
                    const isScrolledToBottom = term.scrollHeight - term.clientHeight <= term.scrollTop + 50;
                    
                    if(event.data.startsWith("GOLIATH_ALERT:")) {
                        try {
                            const alertData = JSON.parse(event.data.substring(14));
                            const toastHtml = `
                            <div class="toast show bg-danger text-white mb-2" role="alert">
                                <div class="toast-header bg-dark text-danger border-danger">
                                    <strong class="me-auto">🚨 HVT ALERT DETECTED</strong>
                                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
                                </div>
                                <div class="toast-body">
                                    Watchlist Match: <b>${alertData.keyword}</b><br>Kilde: ${alertData.module}<br>Target: ${alertData.target}
                                </div>
                            </div>`;
                            document.getElementById('toastContainer').insertAdjacentHTML('beforeend', toastHtml);
                        } catch(e) {}
                    } else {
                        term.textContent += event.data;
                        if(isScrolledToBottom) term.scrollTop = term.scrollHeight;
                    }
                };
                ws.onerror = function() { term.textContent += "\\n[!] WebSocket Fejl. Kører WebSockets-dæmonen?"; };
                </script>
            {% endif %}
        </div>
    </body>
    </html>
    """
    engine = Engine(app_dirs=False)
    template = engine.from_string(html_template)
    context = Context({"records": records, "stats": stats, "error_msg": error_msg, "query": query, "scheduled_hunts": scheduled_hunts, "active_operations": active_operations, "emails": emails_qs, "credentials": creds_qs, "cred_stats": cred_stats, "email_stats": email_stats, "watchlist_items": watchlist_items, "security_alerts": security_alerts, "master_personas": master_personas, "request": request})
    return HttpResponse(template.render(context))

@login_required
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

@login_required
def get_persona(request, persona_id):
    """API Endpoint: Returnerer en 360-graders identitetsprofil (Batch 11)."""
    try:
        persona = MasterPersona.objects.get(id=persona_id)
        data = {
            "id": persona.id, "target": persona.target,
            "name": persona.name, "email": persona.email,
            "phone": persona.phone, "social_handle": persona.social_handle,
            "confidence_score": persona.confidence_score,
            "is_verified": persona.is_verified,
            "raw_data_ref": json.loads(persona.raw_data_ref) if persona.raw_data_ref else {}
        }
        return JsonResponse({"status": "success", "persona": data})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=404)

@login_required
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
        except Exception:
            pass
            
    # GOLIATH V54: Predictive Linking Integration
    try:
        from core.nexus import nexus as nexus_engine
        if nexus_engine:
            for pred in nexus_engine.predict_links():
                add_node(pred['source'], "Unknown")
                add_node(pred['target'], "Unknown")
                # D3.js / Vis.js styler den som stiplet pink linje
                edges.append({"from": pred['source'], "to": pred['target'], "label": pred['label'], "dashes": True, "color": {"color": "#ff007f"}})
    except Exception as e: 
        pass
        
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
                    from django.utils import timezone
                    celery_app.send_task("execute_goliath_module", args=[module_id, target])
                    return JsonResponse({"status": "success", "message": f"Celery Task i kø for {target}!"})
                except Exception: pass
            
            # Fallback til baggrundstråd (Zero-Crash OPSEC)
            import uuid
            from django.utils import timezone
            tid = str(uuid.uuid4())
            ActiveOperation.objects.create(task_id=tid, module_id=str(module_id), target=target, status="Processing", created_at=timezone.now())
            
            def run_fallback():
                res = subprocess.run([sys.executable, "main.py", "-t", target, "-m", str(module_id)])
                try:
                    op = ActiveOperation.objects.get(task_id=tid)
                    op.status = "Success" if res.returncode == 0 else "Failed"
                    op.save()
                except: pass
                
            threading.Thread(target=run_fallback, daemon=True).start()
            return JsonResponse({"status": "success", "message": f"Fallback: Tråd startet direkte for {target}!"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method Not Allowed"}, status=405)

@csrf_exempt
def handle_schedule(request, hunt_id=None):
    """API Endpoint: Opretter eller sletter cronjobs for Reprohack-style automatisering."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ScheduledHunt.objects.create(
                target=data.get('target'),
                module_id=data.get('module_id'),
                interval_minutes=int(data.get('interval_minutes', 60))
            )
            return JsonResponse({"status": "success", "message": "Overvågning aktiveret!"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    elif request.method == 'DELETE' and hunt_id:
        try:
            ScheduledHunt.objects.filter(id=hunt_id).delete()
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method Not Allowed"}, status=405)

@csrf_exempt
def handle_watchlist(request, item_id=None):
    """API Endpoint: GOLIATH V53 HVT Watchlist Manager."""
    if request.method == 'POST' and not item_id:
        data = json.loads(request.body)
        WatchlistItem.objects.create(keyword=data.get('keyword'))
        return JsonResponse({"status": "success"})
    elif request.method == 'DELETE' and item_id:
        WatchlistItem.objects.filter(id=item_id).delete()
        return JsonResponse({"status": "success"})
    return JsonResponse({"error": "Method Not Allowed"}, status=405)

@csrf_exempt
def handle_alerts(request, alert_id=None):
    """API Endpoint: Markerer sikkerhedsalarmer som læst."""
    if request.method == 'POST' and alert_id:
        alert = SecurityAlert.objects.filter(id=alert_id).first()
        if alert: alert.is_read = True; alert.save()
        return JsonResponse({"status": "success"})
    return JsonResponse({"error": "Method Not Allowed"}, status=405)

@login_required
@csrf_exempt
def verify_persona(request, persona_id):
    """API Endpoint: GOLIATH V56 Manuel verifikation og scoring af efterretninger."""
    if request.method == 'POST':
        data = json.loads(request.body)
        with connection.cursor() as cursor:
            cursor.execute("UPDATE master_personas SET is_verified = 1 WHERE id = ?", [persona_id])
            cursor.execute("INSERT INTO persona_reviews (persona_id, operator_name, comment, rating, timestamp) VALUES (?, ?, ?, ?, ?)",
                           [persona_id, request.user.username, data.get('comment', ''), data.get('rating', 5), datetime.now()])
        return JsonResponse({"status": "success", "message": "Persona verificeret via Peer-Review!"})
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

@login_required
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

@login_required
def download_export(request):
    """Downloader den nyeste AES-krypterede eksport (Batch 15)."""
    loot_dir = session.get("loot_folder", "workspaces/standard_sag")
    exports = glob.glob(os.path.join(loot_dir, "GOLIATH_EXPORT_*.aes"))
    if exports:
        latest = max(exports, key=os.path.getctime)
        with open(latest, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(latest)}"'
            return response
    return JsonResponse({"error": "Ingen eksport fundet. Kør Modul 30 mod et target først for at generere den."})

@login_required
def download_verified(request):
    """GOLIATH V56: Downloader et dynamisk genereret dossier KUN med verificerede fund."""
    target = session.get("name", "")
    if not target:
        return HttpResponse("<script>alert('Intet target valgt i sessionen. Skriv en target-søgning (fx target scor.dk) i terminalen først.'); window.history.back();</script>")
    
    from core.reporter import AutomatedCaseReporter
    reporter = AutomatedCaseReporter()
    filepath = reporter.generate_verified_dossier(target)
    with open(filepath, 'r', encoding='utf-8') as f:
        response = HttpResponse(f.read(), content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(filepath)}"'
        return response

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
    path('login/', login_view),
    path('logout/', logout_view),
    path('record/<int:record_id>/', record_detail),
    path('graph/', network_graph),
    path('api/v1/trigger/', trigger_scan),
    path('api/v1/schedule/', handle_schedule),
    path('api/v1/schedule/<int:hunt_id>/', handle_schedule),
    path('api/v1/watchlist/', handle_watchlist),
    path('api/v1/watchlist/<int:item_id>/', handle_watchlist),
    path('api/v1/alerts/<int:alert_id>/', handle_alerts),
    path('api/v1/record/<int:record_id>/', delete_record),
    path('api/v1/upload/', handle_upload),
    path('api/v1/loot/', api_datalake),
    path('api/v1/download_report/', download_report),
    path('api/v1/download_verified/', download_verified),
    path('api/v1/download_export/', download_export),
    path('api/v1/intelligence/persona/<int:persona_id>/', get_persona),
    path('api/v1/intelligence/verify/<int:persona_id>/', verify_persona),
]

# =====================================================================
# 5. ASYNKRON WEBSOCKET DAEMON (PORT 8001)
# =====================================================================
async def log_tailer(websocket, path):
    """Tailer worker loggen asynkront og pusher via WebSockets."""
    log_file = "logs/celery_worker.log"
    alert_pipe = "logs/ws_alerts.pipe"
    Path(alert_pipe).touch() # Sikrer filen eksisterer
    try:
        with open(log_file, "r", encoding='utf-8') as f, open(alert_pipe, "r", encoding='utf-8') as a:
            f.seek(0, 2) # Spring til slutningen
            a.seek(0, 2)
            while True:
                line = f.readline()
                if line: await websocket.send(line)
                
                alert = a.readline()
                if alert: await websocket.send("GOLIATH_ALERT:" + alert)
                
                if not line and not alert:
                    await asyncio.sleep(0.1)
    except Exception as e:
        await websocket.send(f"[WS ERROR] Kunne ikke læse loggen: {e}")

def start_ws_server():
    if not websockets: return
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    start_server = websockets.serve(log_tailer, "0.0.0.0", 8001)
    loop.run_until_complete(start_server)
    loop.run_forever()

def run_server(port="8000"):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', int(port))) == 0:
                print(f"\n{C.YELLOW}[!] Port {port} er allerede i brug. Web serveren kører muligvis allerede!{C.RESET}")
                return
                
        # Spinder WebSocket serveren op i baggrunden
        threading.Thread(target=start_ws_server, daemon=True).start()
        
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
