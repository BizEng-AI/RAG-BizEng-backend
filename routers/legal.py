from __future__ import annotations

import html

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import EmailStr
from sqlalchemy.orm import Session

from account_lifecycle import authenticate_user_by_email_and_password, delete_user_account
from db import get_db
from request_limits import count_hits, extract_client_ip, record_hit, reset_key
from settings import (
    ACCOUNT_DELETE_FAILURE_EMAIL_LIMIT,
    ACCOUNT_DELETE_FAILURE_IP_LIMIT,
    ACCOUNT_DELETE_FAILURE_WINDOW_SECONDS,
    APP_PUBLIC_NAME,
    PUBLIC_BASE_URL,
    SUPPORT_EMAIL,
)

router = APIRouter(tags=["legal"])

DELETE_SCOPE_IP = "account_delete_ip"
DELETE_SCOPE_EMAIL = "account_delete_email"


def _normalized_email(email: str) -> str:
    return email.strip().lower()


def _public_base_url(request: Request) -> str:
    if PUBLIC_BASE_URL:
        return PUBLIC_BASE_URL
    return str(request.base_url).rstrip("/")


def _enforce_delete_limits(request: Request, email: str) -> tuple[str, str]:
    email_key = _normalized_email(email)
    ip_key = extract_client_ip(request)

    if count_hits(DELETE_SCOPE_IP, ip_key, window_seconds=ACCOUNT_DELETE_FAILURE_WINDOW_SECONDS) >= ACCOUNT_DELETE_FAILURE_IP_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many deletion attempts from this network. Please try again later."
        )
    if count_hits(DELETE_SCOPE_EMAIL, email_key, window_seconds=ACCOUNT_DELETE_FAILURE_WINDOW_SECONDS) >= ACCOUNT_DELETE_FAILURE_EMAIL_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many deletion attempts for this account. Please try again later."
        )

    return email_key, ip_key


def _record_delete_failure(email_key: str, ip_key: str) -> None:
    record_hit(DELETE_SCOPE_EMAIL, email_key, window_seconds=ACCOUNT_DELETE_FAILURE_WINDOW_SECONDS)
    record_hit(DELETE_SCOPE_IP, ip_key, window_seconds=ACCOUNT_DELETE_FAILURE_WINDOW_SECONDS)


def _render_page(title: str, body_html: str) -> HTMLResponse:
    page = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{html.escape(title)}</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f5efe6;
        --panel: rgba(255, 255, 255, 0.92);
        --text: #1f1d1a;
        --muted: #5d5a56;
        --accent: #0c6c8c;
        --danger: #a43c2f;
        --border: rgba(31, 29, 26, 0.12);
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: "Segoe UI", system-ui, sans-serif;
        background:
          radial-gradient(circle at top left, rgba(12, 108, 140, 0.18), transparent 38%),
          radial-gradient(circle at top right, rgba(217, 150, 61, 0.18), transparent 34%),
          linear-gradient(180deg, #fbf7f2 0%, var(--bg) 100%);
        color: var(--text);
      }}
      main {{
        max-width: 840px;
        margin: 0 auto;
        padding: 40px 20px 72px;
      }}
      .panel {{
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 24px;
        padding: 28px;
        box-shadow: 0 24px 60px rgba(31, 29, 26, 0.08);
      }}
      h1, h2 {{ margin-top: 0; }}
      h1 {{ font-size: 2rem; margin-bottom: 0.6rem; }}
      h2 {{ margin-top: 1.75rem; font-size: 1.15rem; }}
      p, li {{ line-height: 1.6; color: var(--muted); }}
      a {{ color: var(--accent); }}
      form {{
        margin-top: 1.5rem;
        display: grid;
        gap: 12px;
      }}
      label {{
        display: grid;
        gap: 6px;
        color: var(--text);
        font-weight: 600;
      }}
      input {{
        width: 100%;
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 12px 14px;
        font: inherit;
      }}
      button {{
        border: 0;
        border-radius: 999px;
        padding: 12px 18px;
        font: inherit;
        font-weight: 700;
        color: white;
        background: var(--accent);
        cursor: pointer;
      }}
      button.danger {{ background: var(--danger); }}
      .callout {{
        margin-top: 16px;
        padding: 14px 16px;
        border-radius: 16px;
        background: rgba(164, 60, 47, 0.10);
        color: var(--danger);
        border: 1px solid rgba(164, 60, 47, 0.18);
      }}
      .success {{
        background: rgba(12, 108, 140, 0.10);
        color: #0b5b75;
        border-color: rgba(12, 108, 140, 0.18);
      }}
      .eyebrow {{
        display: inline-block;
        margin-bottom: 12px;
        padding: 6px 12px;
        border-radius: 999px;
        background: rgba(12, 108, 140, 0.10);
        color: var(--accent);
        font-size: 0.9rem;
        font-weight: 700;
        letter-spacing: 0.02em;
      }}
      ul {{ padding-left: 1.2rem; }}
      code {{
        padding: 0.15rem 0.35rem;
        border-radius: 0.4rem;
        background: rgba(31, 29, 26, 0.06);
      }}
    </style>
  </head>
  <body>
    <main>
      <section class="panel">
        {body_html}
      </section>
    </main>
  </body>
</html>"""
    return HTMLResponse(page)


@router.get("/legal/privacy", response_class=HTMLResponse)
def privacy_policy(request: Request) -> HTMLResponse:
    base_url = html.escape(_public_base_url(request))
    support_email = html.escape(SUPPORT_EMAIL)
    app_name = html.escape(APP_PUBLIC_NAME)
    body = f"""
<div class="eyebrow">Privacy Policy</div>
<h1>{app_name}</h1>
<p>This policy explains what data {app_name} handles, why we handle it, and how you can delete your account and associated data.</p>

<h2>Contact</h2>
<p>If you have questions about privacy or deletion, contact <a href="mailto:{support_email}">{support_email}</a>.</p>

<h2>Data we collect</h2>
<ul>
  <li>Account details: email address, display name, optional group number, hashed password, and issued auth tokens.</li>
  <li>Learning progress metadata: exercise attempts, timestamps, scores, feature usage, and weighted AI usage counters.</li>
  <li>Roleplay session data: roleplay dialogue, corrections, and summaries that let you resume a roleplay session.</li>
  <li>Speech inputs you choose to send: audio files used for speech-to-text and pronunciation scoring are processed to produce the requested result.</li>
</ul>

<h2>How we use data</h2>
<ul>
  <li>To create and secure your account.</li>
  <li>To deliver chat, roleplay, pronunciation, text-to-speech, and speech-to-text features.</li>
  <li>To show your progress history and basic classroom analytics.</li>
  <li>To enforce abuse protections and low-volume usage limits.</li>
</ul>

<h2>Sharing and processors</h2>
<p>We use service providers to process AI and speech requests, including Azure OpenAI, Azure Speech, and related infrastructure configured for the app. We do not sell personal data.</p>

<h2>Security</h2>
<ul>
  <li>Production traffic is intended to run over HTTPS.</li>
  <li>Passwords are stored as strong password hashes, not plaintext.</li>
  <li>The Android app stores auth tokens in encrypted storage.</li>
  <li>Microphone access is requested only when you choose a speaking feature.</li>
</ul>

<h2>Retention and deletion</h2>
<ul>
  <li>Account profile data, progress metadata, AI usage records, refresh tokens, and roleplay sessions are kept until you delete your account.</li>
  <li>Speech uploads are used to generate the requested result and temporary server files are removed after processing.</li>
  <li>When you delete your account, the app deletes your account record, auth tokens, progress data, AI usage records, and stored roleplay sessions managed by this service.</li>
  <li>Minimal operational logs without user message content may remain temporarily in hosting logs according to platform retention settings.</li>
 </ul>

<h2>Your choices</h2>
<p>You can delete your account inside the app or from the web at <a href="{base_url}/legal/account-deletion">{base_url}/legal/account-deletion</a>.</p>
"""
    return _render_page("Privacy Policy", body)


@router.get("/legal/account-deletion", response_class=HTMLResponse)
def account_deletion_page(request: Request, message: str | None = None, error: str | None = None) -> HTMLResponse:
    base_url = html.escape(_public_base_url(request))
    support_email = html.escape(SUPPORT_EMAIL)
    message_html = ""
    if message:
        message_html = f'<div class="callout success">{html.escape(message)}</div>'
    elif error:
        message_html = f'<div class="callout">{html.escape(error)}</div>'

    body = f"""
<div class="eyebrow">Account Deletion</div>
<h1>Delete your {html.escape(APP_PUBLIC_NAME)} account</h1>
<p>You can delete your account permanently from inside the app, or use this page outside the app. This action removes your stored account profile, refresh tokens, progress data, AI usage records, and roleplay sessions managed by this service.</p>
<p>If you need help, contact <a href="mailto:{support_email}">{support_email}</a>. You can also review the <a href="{base_url}/legal/privacy">privacy policy</a>.</p>
{message_html}
<form method="post" action="{base_url}/legal/account-deletion">
  <label>Email
    <input type="email" name="email" autocomplete="username" required />
  </label>
  <label>Current password
    <input type="password" name="current_password" autocomplete="current-password" required />
  </label>
  <label>Type <code>DELETE</code> to confirm
    <input type="text" name="confirm_phrase" placeholder="DELETE" required />
  </label>
  <button class="danger" type="submit">Delete account permanently</button>
</form>
"""
    return _render_page("Account Deletion", body)


@router.post("/legal/account-deletion", response_class=HTMLResponse)
def delete_account_via_web(
    request: Request,
    email: EmailStr = Form(...),
    current_password: str = Form(...),
    confirm_phrase: str = Form(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    if confirm_phrase != "DELETE":
        return account_deletion_page(
            request,
            error='Please type DELETE exactly to confirm account removal.',
        )

    email_key, ip_key = _enforce_delete_limits(request, str(email))
    user = authenticate_user_by_email_and_password(db, str(email), current_password)
    if not user:
        _record_delete_failure(email_key, ip_key)
        return HTMLResponse(
            content=account_deletion_page(
                request,
                error="We could not verify those credentials. Please try again."
            ).body,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    delete_user_account(db, user)
    reset_key(DELETE_SCOPE_EMAIL, email_key)
    return account_deletion_page(
        request,
        message="Your account has been deleted successfully."
    )
