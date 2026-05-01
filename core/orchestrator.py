--- /dev/null
+++ b/home/hugo/omni_hunter/core/orchestrator.py
@@ -0,0 +1,59 @@
+# -*- coding: utf-8 -*-
+"""
+🚀 OMNI_HUNTER V54: DEEP SEARCH ORCHESTRATOR
+📌 Formål: Autonom evaluering af Master Personas og auto-dispatching af OSINT moduler.
+"""
+import sqlite3
+from pathlib import Path
+from core.utils import session, logger
+import threading
+
+class DeepSearchOrchestrator:
+    """GOLIATH V54: Den automatiske intelligens-officer."""
+    
+    def __init__(self):
+        self.db_path = Path(session.get("loot_folder", "loot_evidence")) / "omni_datalake.db"
+
+    def analyze_persona_and_dispatch(self, persona_id: int):
+        if not self.db_path.exists(): 
+            logger.error("[ORCHESTRATOR] Datalake ikke fundet.")
+            return
+            
+        try:
+            with sqlite3.connect(self.db_path) as conn:
+                cursor = conn.cursor()
+                cursor.execute("SELECT target, email, phone, name, social_handle, last_ip FROM master_personas WHERE id=?", (persona_id,))
+                row = cursor.fetchone()
+                if not row: 
+                    logger.warning(f"[ORCHESTRATOR] Persona ID {persona_id} findes ikke.")
+                    return
+                
+                target, email, phone, name, handle, ip = row
+                
+                # Definerer angrebskæder baseret på tilgængelig data
+                tasks = []
+                if email:
+                    tasks.append(("03", email)) # Breach Intelligence
+                    tasks.append(("09", email)) # MailRip
+                if phone:
+                    tasks.append(("04", phone)) # Phone Intel / Telecom
+                if handle or name:
+                    tasks.append(("02", handle or name)) # Social Profiler
+                if ip and ip != "Ukendt":
+                    tasks.append(("06", ip)) # Omni Infra Tracker
+                    
+                self._dispatch_tasks(tasks, target)
+                logger.info(f"[ORCHESTRATOR] Affyrede {len(tasks)} autonome Celery-tasks for Persona #{persona_id} ({target})")
+        except Exception as e:
+            logger.error(f"Orchestrator fejl: {e}")
+
+    def _dispatch_tasks(self, tasks, original_target):
+        try:
+            from core.web_server import celery_app
+            if celery_app:
+                for mod_id, t in tasks:
+                    celery_app.send_task("execute_goliath_module", args=[mod_id, t])
+                return
+        except ImportError: pass
+        
+        # OPSEC Fallback til baggrundstråde hvis Celery er nede
+        import subprocess, sys
+        for mod_id, t in tasks:
+            threading.Thread(target=lambda m=mod_id, tgt=t: subprocess.run([sys.executable, "main.py", "-t", tgt, "-m", m]), daemon=True).start()
