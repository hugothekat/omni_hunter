# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER - THE NATIVE API SYNDICATE (core/api_syndicate.py)
📌 Formål: Asynkron, native kommunikation med Threat Intel databaser uden ustabile PyPI wrappers.
"""
import aiohttp
import asyncio
import random
import socket
import struct
from fake_useragent import UserAgent
from typing import Dict, Any
from core.utils import logger
from core.config_vault import vault

class ThreatIntelSyndicate:
    def __init__(self):
        # Trækker nøgler dynamisk fra The Secure Vault
        self.keys = vault.get("api_keys") or {} if vault else {}
        self.st_key = self.keys.get("securitytrails_api_key", "")
        self.otx_key = self.keys.get("alienvault_api_key", "")
        self.gn_key = self.keys.get("greynoise_api_key", "")
        self.abuse_key = self.keys.get("abuseipdb_api_key", "")

    async def _async_get(self, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        max_attempts = 4
        attempt = 0
        
        while attempt < max_attempts:
            try:
                # Aktiv Evasion: IP Spoofing og User-Agent rotation asynkront
                spoofed_ip = socket.inet_ntoa(struct.pack('>I', random.randint(0x01000000, 0xEFFFFFFF)))
                headers['X-Forwarded-For'] = spoofed_ip
                headers['X-Real-IP'] = spoofed_ip
                headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                try: 
                    headers['User-Agent'] = UserAgent().random
                except Exception: 
                    headers['User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, timeout=15) as response:
                        if response.status in [429, 403]:
                            attempt += 1
                            logger.warning(f"⚠️ [ASYNC WAF/RATE-LIMIT] Blokeret af {url}. Evasion attempt {attempt}/{max_attempts}...")
                            await asyncio.sleep(random.uniform(1.5, 4.0) * attempt)
                            continue
                            
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 401:
                            return {"error": "Unauthorized / Invalid API Key"}
                        elif response.status == 404:
                            return {"error": "Not Found"}
                        else:
                            return {"error": f"HTTP {response.status}"}
            except Exception as e:
                logger.error(f"API Syndicate Fetch Error mod {url}: {e}")
                return {"error": str(e)}
        return {"error": "Max retries exceeded during WAF Evasion."}

    async def _async_post(self, url: str, headers: Dict[str, str], data: Dict[str, str]) -> Dict[str, Any]:
        """NY V43: POST-version af _async_get med samme evasions-logik."""
        max_attempts = 4
        attempt = 0
        
        while attempt < max_attempts:
            try:
                # Aktiv Evasion: IP Spoofing og User-Agent rotation asynkront
                spoofed_ip = socket.inet_ntoa(struct.pack('>I', random.randint(0x01000000, 0xEFFFFFFF)))
                headers['X-Forwarded-For'] = spoofed_ip
                try: 
                    headers['User-Agent'] = UserAgent().random
                except Exception: 
                    headers['User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, data=data, timeout=15) as response:
                        if response.status in [429, 403]:
                            attempt += 1
                            logger.warning(f"⚠️ [ASYNC WAF/RATE-LIMIT] Blokeret af {url}. Evasion attempt {attempt}/{max_attempts}...")
                            await asyncio.sleep(random.uniform(1.5, 4.0) * attempt)
                            continue
                            
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 401:
                            return {"error": "Unauthorized / Invalid API Key"}
                        else:
                            return {"error": f"HTTP {response.status}"}
            except Exception as e:
                logger.error(f"API Syndicate POST Error mod {url}: {e}")
                return {"error": str(e)}
        return {"error": "Max retries exceeded during WAF Evasion."}

    async def check_securitytrails(self, domain_or_ip: str) -> Dict[str, Any]:
        """Henter historisk DNS og subdomæner fra SecurityTrails."""
        if not self.st_key: return {"error": "No SecurityTrails API Key"}
        url = f"https://api.securitytrails.com/v1/domain/{domain_or_ip}"
        headers = {"APIKEY": self.st_key, "accept": "application/json"}
        return await self._async_get(url, headers)

    async def check_alienvault(self, indicator: str, indicator_type: str = "IPv4") -> Dict[str, Any]:
        """Henter Open Threat Exchange (OTX) pulses."""
        if not self.otx_key: return {"error": "No AlienVault API Key"}
        url = f"https://otx.alienvault.com/api/v1/indicators/{indicator_type}/{indicator}/general"
        headers = {"X-OTX-API-KEY": self.otx_key}
        return await self._async_get(url, headers)

    async def check_greynoise(self, ip: str) -> Dict[str, Any]:
        """Tjekker om IP'en er en kendt internet-scanner (Noise) eller en RIOT (Legitim service)."""
        if not self.gn_key: return {"error": "No GreyNoise API Key"}
        url = f"https://api.greynoise.io/v3/community/{ip}"
        headers = {"key": self.gn_key, "accept": "application/json"}
        return await self._async_get(url, headers)

    async def check_abuseipdb(self, ip: str) -> Dict[str, Any]:
        """NY V43: Tjekker IP-rygte på AbuseIPDB."""
        if not self.abuse_key: return {"error": "No AbuseIPDB API Key"}
        url = f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip}&maxAgeInDays=90"
        headers = {"Key": self.abuse_key, "Accept": "application/json"}
        return await self._async_get(url, headers)

    async def check_urlhaus(self, url_to_check: str) -> Dict[str, Any]:
        """NY V43: Tjekker om en URL er kendt for malware-distribution via URLhaus."""
        url = "https://urlhaus-api.abuse.ch/v1/url/"
        data = {'url': url_to_check}
        headers = {} # Ingen auth nødvendig
        return await self._async_post(url, headers, data)

# Global eksport af syndikatet
syndicate = ThreatIntelSyndicate()
