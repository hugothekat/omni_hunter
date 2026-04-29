# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER - THE NATIVE API SYNDICATE (core/api_syndicate.py)
📌 Formål: Asynkron, native kommunikation med Threat Intel databaser uden ustabile PyPI wrappers.
"""
import aiohttp
import asyncio
from typing import Dict, Any
from core.utils import logger
from core.config_vault import vault

class ThreatIntelSyndicate:
    def __init__(self):
        # Trækker nøgler dynamisk fra The Secure Vault
        self.keys = vault.get("api_keys") if vault else {}
        self.st_key = self.keys.get("securitytrails_api_key", "")
        self.otx_key = self.keys.get("alienvault_api_key", "")
        self.gn_key = self.keys.get("greynoise_api_key", "")

    async def _async_get(self, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status in [401, 403]:
                        return {"error": "Unauthorized / Invalid API Key"}
                    elif response.status == 404:
                        return {"error": "Not Found"}
                    else:
                        return {"error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"API Syndicate Fetch Error: {e}")
            return {"error": str(e)}

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

# Global eksport af syndikatet
syndicate = ThreatIntelSyndicate()
