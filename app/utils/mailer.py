import os
import smtplib
from email.mime.text import MIMEText


def get_client_url():
    client_url = os.getenv("CLIENT_URL", "https://jesselzapanta09.github.io/railmanager").strip()
    return client_url.rstrip("/")


def build_client_link(path, token):
    client_url = get_client_url()
    clean_path = path.lstrip("/")
    return f"{client_url}/{clean_path}?token={token}"


def build_email_template(title, intro, button_text, button_url, footer_note):
    return f"""
    <!DOCTYPE html>
    <html>
      <body style="margin:0;padding:0;background:#f4f7fb;font-family:Arial,sans-serif;color:#1f2937;">
        <div style="max-width:600px;margin:0 auto;padding:32px 20px;">
          <div style="background:#ffffff;border-radius:16px;padding:32px;border:1px solid #e5e7eb;box-shadow:0 8px 24px rgba(15,23,42,0.08);">
            <div style="text-align:center;margin-bottom:24px;">
              <h1 style="margin:0;font-size:24px;color:#111827;">RailManager</h1>
              <p style="margin:8px 0 0;font-size:14px;color:#6b7280;">Account Security Notification</p>
            </div>

            <h2 style="margin:0 0 16px;font-size:22px;color:#111827;">{title}</h2>
            <p style="margin:0 0 24px;font-size:15px;line-height:1.7;color:#374151;">{intro}</p>

            <div style="margin:32px 0;text-align:center;">
              <a href="{button_url}" style="display:inline-block;background:#2563eb;color:#ffffff;text-decoration:none;padding:14px 24px;border-radius:10px;font-weight:bold;font-size:15px;">
                {button_text}
              </a>
            </div>

            <p style="margin:0 0 12px;font-size:14px;color:#4b5563;">If the button does not work, copy and paste this link into your browser:</p>
            <p style="margin:0 0 24px;word-break:break-all;">
              <a href="{button_url}" style="color:#2563eb;text-decoration:none;">{button_url}</a>
            </p>

            <div style="padding-top:20px;border-top:1px solid #e5e7eb;">
              <p style="margin:0;font-size:13px;line-height:1.6;color:#6b7280;">{footer_note}</p>
            </div>
          </div>
        </div>
      </body>
    </html>
    """


def send_email(to, subject, html):
    smtp_user = os.getenv("GMAIL_USER")
    smtp_pass = os.getenv("GMAIL_APP_PASS")

    if not smtp_user or not smtp_pass:
        print("[Mailer] SMTP credentials are not configured. Skipping email send.")
        return

    msg = MIMEText(html, "html")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        print("[Mailer] Email sent")
    except Exception as e:
        print("[Mailer ERROR]", e)


def send_verification_email(email, username, token):
    url = build_client_link("verify-email", token)
    html = build_email_template(
        title=f"Verify your email, {username}",
        intro="Welcome to RailManager. Please confirm your email address to activate your account and continue using the system.",
        button_text="Verify Email",
        button_url=url,
        footer_note="This verification link will expire automatically. If you did not create this account, you can safely ignore this email.",
    )
    send_email(email, "RailManager Email Verification", html)


def send_reset_email(email, username, token):
    url = build_client_link("reset-password", token)
    html = build_email_template(
        title=f"Reset your password, {username}",
        intro="We received a request to reset your RailManager password. Use the button below to set a new password securely.",
        button_text="Reset Password",
        button_url=url,
        footer_note="If you did not request a password reset, you can ignore this email. Your account will remain secure.",
    )
    send_email(email, "RailManager Password Reset", html)
