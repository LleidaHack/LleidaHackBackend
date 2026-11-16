"""Private bearer-link landing page, usable without a mentor/staff login."""

from html import escape

from src.utils.apple_wallet import participant_role, wallet_url
from src.utils.qr import ticket_qr_url


def ticket_page(settings, event, user):
    wallet = wallet_url(settings, event.id, user.code)
    action = (
        f'<a class="button" href="{escape(wallet, quote=True)}">Afegir a Apple Wallet</a>'
        if wallet
        else "<p>Apple Wallet encara no està disponible. Pots utilitzar aquest QR.</p>"
    )
    return f'''<!doctype html><html lang="ca"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer"><title>Entrada · {escape(event.name)}</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;padding:32px 20px;background:#202020;color:#f7f5ef;font:17px/1.5 system-ui,sans-serif}}
main{{max-width:440px;margin:auto}}h1{{font-size:30px;line-height:1.2;margin:0 0 24px}}h2{{font-size:22px;margin:24px 0 4px}}
p{{margin:8px 0 20px}}.qr{{background:#fff;padding:20px;border-radius:12px;display:block;width:min(100%,300px);height:auto;margin:28px auto}}
.button{{display:block;text-align:center;background:#ff7430;color:#202020;padding:14px 20px;border-radius:8px;font-weight:700;text-decoration:none}}
a:focus-visible{{outline:3px solid #97cef2;outline-offset:4px}}.role{{color:#ffb48c}}code{{overflow-wrap:anywhere}}
</style></head><body><main><h1>{escape(event.name)}</h1>
<h2>{escape(user.name or "")}</h2><p class="role">{escape(participant_role(user))}</p>
<p>Mostra aquest QR a l’entrada per vincular-lo amb la teva acreditació.</p>
<img class="qr" alt="QR personal d’entrada" width="300" height="300" src="{escape(ticket_qr_url(event.id, user.code), quote=True)}">
<p><code>{escape(user.code)}</code></p>{action}
<p>Aquesta entrada és personal. Guarda l’enllaç i no el comparteixis.</p></main></body></html>'''
