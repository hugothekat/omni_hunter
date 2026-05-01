#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 GOLIATH PROXY SNIPER
📌 Formål: Automatisk høst og verifikation af friske Elite Proxies.
"""
import asyncio
import aiohttp
import time
from pathlib import Path
import sys
import subprocess

# GOLIATH AUTO-HEAL: SOCKS5 understøttelse kræver aiohttp-socks
try:
    from aiohttp_socks import ProxyConnector
except ImportError:
    print("\033[93m[*] SOCKS5-modul mangler. Engagerer Auto-Heal (installerer aiohttp-socks)...\033[0m")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp-socks"], stdout=subprocess.DEVNULL)
    from aiohttp_socks import ProxyConnector

PROXY_API_URL = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=5000&country=all&ssl=all&anonymity=elite"
TEST_URL = "http://httpbin.org/ip"
OUTPUT_FILE = Path("/home/hugo/omni_hunter/proxies.txt")

async def test_proxy(proxy: str, valid_proxies: list):
    """Tester asynkront om SOCKS5-proxyen kan gennemføre et kald inden for 10 sekunder."""
    proxy_url = f"socks5://{proxy}"
    try:
        connector = ProxyConnector.from_url(proxy_url)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(TEST_URL, timeout=10) as response:
                if response.status == 200:
                    valid_proxies.append(proxy_url)
                    print(f"[\033[92m+\033[0m] Elite SOCKS5 fundet: {proxy_url}")
    except Exception:
        pass # Ignorer døde proxies stealthy

async def main():
    print("\033[96m[*] Initierer GOLIATH Proxy Sniper...\033[0m")
    print(f"[*] Henter friske SOCKS5 kandidater fra: {PROXY_API_URL}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(PROXY_API_URL) as response:
                raw_proxies = await response.text()
                proxy_list = [p.strip() for p in raw_proxies.splitlines() if p.strip()]
    except Exception as e:
        print(f"\033[91m[!] Netværksfejl ved hentning af proxy-liste: {e}\033[0m")
        return

    print(f"[*] Fandt {len(proxy_list)} kandidater. Påbegynder aggressiv asynkron verifikation...")
    valid_proxies = []
    
    start_time = time.time()
    tasks = [test_proxy(p, valid_proxies) for p in proxy_list]
    await asyncio.gather(*tasks)
        
    elapsed = time.time() - start_time
    
    if valid_proxies:
        OUTPUT_FILE.write_text("\n".join(valid_proxies))
        print(f"\n\033[92m[✓] Mission fuldført på {elapsed:.2f} sekunder!\033[0m")
        print(f"\033[92m[✓] {len(valid_proxies)} friske proxies gemt i {OUTPUT_FILE}\033[0m")
    else:
        print("\n\033[91m[!] Ingen proxies overlevede testen. Prøv igen senere.\033[0m")

if __name__ == "__main__":
    asyncio.run(main())