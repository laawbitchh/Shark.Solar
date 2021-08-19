import redis
import threading
import multiprocessing
from urllib.parse import urlparse
import itertools
import hfuck as hcaptcha
import requests
import xrequests
import time
import json
import random
import secrets
import websocket
import os
#import aiosmtpd.controller

if os.name == "nt":
    import win32process

testsite_array = []

with open('discord_usernames.txt', 'r', encoding='UTF-8') as my_file:
    for line in my_file:
        testsite_array.append(line)    
   
            
            
proxies = []
for line in open('proxies.txt'):
    proxies.append(line.replace('\n', ''))

with open("config.json") as data:
    config = json.load(data)
class Generator:
    def register(captcha):
        try:
            username = random.choice(testsite_array)
            ptype = config['type']
            proxyServer = f"{ptype}://{random.choice(proxies)}"
            sess = requests.Session()
            fingerprint = sess.get("https://discordapp.com/api/v9/experiments", proxies={"http": proxyServer, "https": proxyServer}).json()["fingerprint"]
            sess.headers = {
                "x-fingerprint":fingerprint,
                "x-super-properties":"eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6ImVuLVVTIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzkwLjAuNDQzMC44NSBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiOTAuMC40NDMwLjg1Iiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiIiLCJyZWZlcnJpbmdfZG9tYWluIjoiIiwicmVmZXJyZXJfY3VycmVudCI6IiIsInJlZmVycmluZ19kb21haW5fY3VycmVudCI6IiIsInJlbGVhc2VfY2hhbm5lbCI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjgzMDQwLCJjbGllbnRfZXZlbnRfc291cmNlIjpudWxsfQ==",
                "referrer":"https://discord.com/register",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.115 Safari/537.36"
            };
            data = {
                "captcha_key": captcha,
                "consent": True,
                "email": f"{secrets.token_hex(25)}@gmail.com",
                "fingerprint": fingerprint,
                "date_of_birth": "2001-03-05",
                "gift_code_sku_id": None,
                "invite": config['invite'],
                "username": username
            }
            request = sess.post("https://discord.com/api/v9/auth/register", proxies={"http": proxyServer, "https": proxyServer}, json=data, timeout=4)
            token = request.json()["token"]
            with open("Tokens.txt", "a+") as f:
                f.write(f"{token}\n")
                f.close()
            print(f"[+] Created: {username} - {token[:35]}...")
        except Exception as e:
            pass
class CaptchaSolver:
    WORKER_COUNT = 6
    THREAD_COUNT_PER_WORKER = config['threads']
    HCAPTCHA_BYPASS_TOKEN = config['hcaptcha_accessibility_token']
    SOLVER_PARAMS = dict(database=redis.Redis(host='127.0.0.1', port=6379, db=4), min_answers=0, collect_data=True)
    CHALLENGE_PARAMS = dict(sitekey="f5561ba9-8f1e-40ca-9b5b-a0b3f719ef34", page_url="https://discord.com", actoken=HCAPTCHA_BYPASS_TOKEN)
    def prepareThreads(workerNumber, threadNumber, threadBarrier, threadEvent, proxies, solver):
        threadBarrier.wait()
        threadEvent.wait()
        while True:
            ptype = config['type']
            proxy = random.choice(proxies)
            http_client = requests.Session()
            http_client.proxies={
                "http": f"{ptype}://{proxy}",
                "https": f"{ptype}://{proxy}"
            }
            try:
                token = solver.get_token(**CaptchaSolver.CHALLENGE_PARAMS, http_client=http_client)
                if token:
                    threading.Thread(target=Generator.register, args=(token,)).start();
            except Exception:
                pass
    def prepareWorkers(workerNumber, workerBarrier, proxies):
        cpu_num = workerNumber % multiprocessing.cpu_count()
        solver = hcaptcha.Solver(**CaptchaSolver.SOLVER_PARAMS)
        threadBarrier = threading.Barrier(CaptchaSolver.THREAD_COUNT_PER_WORKER + 1)
        threadEvent = threading.Event()
        threads = [threading.Thread(target=CaptchaSolver.prepareThreads, args=(workerNumber, threadNumber, threadBarrier, threadEvent, proxies, solver)) for threadNumber in range(CaptchaSolver.THREAD_COUNT_PER_WORKER)]
        for thread in threads:
            thread.start()
        threadBarrier.wait()
        workerBarrier.wait()
        threadEvent.set()
        
    def start(self):
        with open("proxies.txt") as fp:
            proxies = fp.read().splitlines()
        workerBarrier = multiprocessing.Barrier(CaptchaSolver.WORKER_COUNT + 1)
        workers = [multiprocessing.Process(target=CaptchaSolver.prepareWorkers, args=(workerNumber, workerBarrier, proxies)) for workerNumber in range(CaptchaSolver.WORKER_COUNT)]
        for worker in workers:
            worker.start()
        workerBarrier.wait()
if __name__ == "__main__":
    CaptchaSolver().start();
