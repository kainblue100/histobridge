"""Download the bbag255 review PDF.

The tokenised silverchair URL breaks when passed through the shell (PowerShell
splits it on the special characters), so it is embedded here instead.
"""
import os
import urllib.request

URL = (
    "https://watermark02.silverchair.com/bbag255.pdf?token=AQECAHi208BE49Ooan9kk"
    "hW_Ercy7Dm3ZL_9Cf3qfKAc485ysgAAAncwggJzBgkqhkiG9w0BBwagggJkMIICYAIBADCCAl"
    "kGCSqGSIb3DQEHATAeBglghkgBZQMEAS4wEQQMDdVWrzn6N1FWVtZuAgEQgIICKgj6bluaKD_W"
    "ILkpdws0KbGJlCMTLqawWZb3WGkE9wIqPaevRd1yPHSlk5q28k-Jeibk1SDsQEV45NVp3t5tU"
    "L7swyp-ypYceb3F1M3fJTk4U_rJYG--bc7t67QABKxo49zf6GKX22Zao2EQg77boRFCtwM4Xi"
    "vmLzv4OReTuGURwfUWk68zjKn6BsWzBdWg22EGHYODSba2ygRenLNbv3bjbIKK1FS9R2Tjdmz"
    "8rrndnCNm3xIT-MQt2kOkx3_4GXWn_E4Y7nAJP8aBpZSe65pp5-dTCBDLl6rTExhkh1p-73jd"
    "jcnkBWTWgf7vgLK8OFEE5Kcg75Y_4TEBDOf6hK2J8rSbffrHPKvzxlEJxV-HzbbBjzJSUhAJ2"
    "83ArbMyoH0FjY7g0wSpQACabb_ZgeTcZ01rhmUrMMUrPyT0OaPCvMPxv8sH37Vi7lk8NpjUae"
    "NNW3S8-1aOnu9Q4FiXQSBN_ZMFwkNbJ_Tz0YFxQ_KxjElQZ0HOR27NU3Kz0VUhEO5DN3oJf6"
    "JApH4RgcAoBpKomGkq_so7xzE7aaMSOrTK8l2NaFqR2R-UmWrf0QW74FgUxvKzMWrSVDJPmK-"
    "GIceoLEeZz36aRvzIyniHOE5F3Gq6CmGRf-4J1lBnnJ-T_1jbR4BlTtSmiSgdf9rwwQmmQ8ew"
    "PLN7hWsuS87T-yPCGZ710ZaFtqpDTzJJH6QmZuObLJujkCrAo8zOwv6C8v_S8RS_0x_LHe84"
)

OUT = r"D:\coda_matlab\histobridge\docs\bbag255.pdf"


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    req = urllib.request.Request(URL, headers={
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0 Safari/537.36"),
        "Accept": "application/pdf,*/*",
    })
    with urllib.request.urlopen(req, timeout=180) as r:
        data = r.read()
        print("status", r.status, "content-type", r.headers.get("Content-Type"))
    with open(OUT, "wb") as f:
        f.write(data)
    print("bytes", len(data))
    print("magic", data[:5])
    if data[:4] != b"%PDF":
        raise SystemExit("not a PDF -- the token has probably expired")


if __name__ == "__main__":
    main()
