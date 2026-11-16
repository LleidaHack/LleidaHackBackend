"""Private bearer-link landing page, usable without a mentor/staff login."""

from html import escape

from src.utils.apple_wallet import participant_role, wallet_enabled
from src.utils.ticket_links import public_ticket_url


def ticket_page(settings, event, user):
    ticket = escape(public_ticket_url(settings, event.id, user.code), quote=True)
    assets = "/entrada/imatges"
    action = (
        f'<a class="wallet" href="{ticket}/apple.pkpass"><img src="{assets}/ticket/add-to-apple-wallet.png" alt="Afegir a Apple Wallet" width="151" height="47"></a>'
        if wallet_enabled(settings)
        else ""
    )
    return f'''<!doctype html><html lang="ca"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer"><title>Entrada · {escape(event.name)}</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;padding:32px 12px;background:#202020;color:#f7f5ef;font:16px/1.7 'Courier New',monospace}}
main{{max-width:600px;margin:auto;background:#2e2e2e}}.top{{background:#ff7430;color:#232323;padding:14px 26px;font-weight:bold;display:flex;align-items:center;justify-content:space-between;gap:16px;font-size:12px}}
.top img{{width:110px;height:auto}}.sky{{background:#97cef2;padding:24px 20px;color:#2e2e2e;text-align:center}}.sky-art{{display:flex;align-items:center;justify-content:space-around;gap:12px}}.cloud{{width:23%;height:auto}}.logo{{width:150px;height:158px;object-fit:contain}}.edition{{font-size:12px;font-weight:bold;letter-spacing:2px;margin:12px 0 0}}
.content{{padding:32px 42px}}h1{{font-size:36px;line-height:1.15;margin:0 0 24px}}h2{{font-size:22px;line-height:1.4;margin:0;overflow-wrap:anywhere}}p{{margin:0 0 18px}}.role{{color:#ffb48c;margin:4px 0 24px;font-weight:bold}}.qr-box{{background:#f7f5ef;border-radius:6px;padding:24px;margin:24px 0;text-align:center}}.qr{{display:block;width:min(100%,260px);height:auto;margin:auto}}.wallet{{display:inline-block;margin:0 0 24px}}.wallet img{{display:block}}a:focus-visible{{outline:3px solid #97cef2;outline-offset:4px}}.footer{{border-top:1px solid #565656;margin-top:28px;padding-top:20px;display:flex;justify-content:space-between;align-items:center;gap:24px}}.footer img{{width:64px;height:auto}}.personal{{font-size:13px;color:#ccc}}.bottom{{height:12px;background:#ff7430}}
@media(max-width:480px){{body{{padding:0}}.content{{padding:28px 22px}}h1{{font-size:32px}}.top{{padding:14px 22px}}}}
</style></head><body><main>
<header class="top"><img src="{assets}/logo_lleidahack_blanc.png" alt="LleidaHack"><span>HACKEPS / 10a EDICIÓ</span></header>
<div class="sky"><div class="sky-art"><img class="cloud" src="{assets}/ticket/cloud-left.png" alt=""><img class="logo" src="{assets}/ticket/hackeps-logo.png" alt="HackEPS · 10a edició"><img class="cloud" src="{assets}/ticket/cloud-right.png" alt=""></div><p class="edition">10 ANYS FENT HACKEPS</p></div>
<div class="content"><h1>La teva entrada</h1><h2>{escape(user.name or "")}</h2><p class="role">{escape(participant_role(user))} · {escape(event.name)}</p>
<p>Mostra aquest QR al check-in per recollir la teva acreditació.</p>
<div class="qr-box"><img class="qr" alt="QR personal d’entrada" width="260" height="260" src="{ticket}/qr.png"></div>{action}
<p class="personal">Aquesta entrada és personal. Guarda l’enllaç i no el comparteixis.</p>
<footer class="footer"><strong>L’equip de LleidaHack</strong><img src="{assets}/ticket/hacker.png" alt=""></footer></div><div class="bottom"></div></main></body></html>'''
