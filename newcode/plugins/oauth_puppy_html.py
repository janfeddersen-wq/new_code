"""Shared HTML templates for OAuth callback pages."""

from __future__ import annotations

from typing import Optional


def oauth_success_html(service_name: str, extra_message: Optional[str] = None) -> str:
    """Return a clean success HTML page for OAuth completion."""
    clean_service = service_name.strip() or "OAuth"
    detail = f"<p class='detail'>{extra_message}</p>" if extra_message else ""
    return (
        "<!DOCTYPE html>"
        "<html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>OAuth Success</title>"
        "<style>"
        "html,body{margin:0;padding:0;height:100%;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background:#0f172a;color:#e2e8f0;}"
        "body{display:flex;align-items:center;justify-content:center;}"
        ".card{width:90%;max-width:480px;padding:48px 40px;background:#1e293b;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,0.4);text-align:center;border:1px solid #334155;}"
        ".icon{font-size:48px;margin-bottom:16px;}"
        "h1{font-size:1.5em;margin:0 0 8px;color:#f1f5f9;}"
        "p{font-size:0.95em;margin:8px 0;color:#94a3b8;line-height:1.5;}"
        ".detail{color:#cbd5e1;}"
        ".countdown{margin-top:24px;font-size:0.85em;color:#64748b;}"
        "</style>"
        "</head><body>"
        "<div class='card'>"
        "<div class='icon'>&#x2705;</div>"
        f"<h1>Authentication Successful</h1>"
        f"<p>{clean_service} has been connected.</p>"
        f"{detail}"
        "<p class='countdown'>This window will close in <span id='t'>3</span>s</p>"
        "</div>"
        "<script>"
        "let s=3,el=document.getElementById('t');"
        "setInterval(()=>{s--;if(s>=0)el.textContent=s;if(s<=0)window.close();},1000);"
        "</script>"
        "</body></html>"
    )


def oauth_failure_html(service_name: str, reason: str) -> str:
    """Return a clean error HTML page for OAuth failure."""
    clean_service = service_name.strip() or "OAuth"
    clean_reason = reason.strip() or "An unexpected error occurred"
    return (
        "<!DOCTYPE html>"
        "<html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>OAuth Error</title>"
        "<style>"
        "html,body{margin:0;padding:0;height:100%;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background:#0f172a;color:#e2e8f0;}"
        "body{display:flex;align-items:center;justify-content:center;}"
        ".card{width:90%;max-width:480px;padding:48px 40px;background:#1e293b;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,0.4);text-align:center;border:1px solid #334155;}"
        ".icon{font-size:48px;margin-bottom:16px;}"
        "h1{font-size:1.5em;margin:0 0 8px;color:#fca5a5;}"
        "p{font-size:0.95em;margin:8px 0;color:#94a3b8;line-height:1.5;}"
        ".reason{color:#f87171;}"
        ".guidance{margin-top:24px;color:#64748b;font-size:0.85em;}"
        "</style>"
        "</head><body>"
        "<div class='card'>"
        "<div class='icon'>&#x274C;</div>"
        f"<h1>{clean_service} Authentication Failed</h1>"
        f"<p class='reason'>{clean_reason}</p>"
        "<p class='guidance'>Please try again from the application.</p>"
        "</div>"
        "</body></html>"
    )
