import os
import imaplib
import email
from email.header import decode_header
from plugins.base import BasePlugin
from core.tool_registry import tool
from automation.os_manager import open_url_tab

class MailPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "mail_plugin"

    @property
    def description(self) -> str:
        return "Checks unread emails and drafts or sends emails via Gmail."

    def register_tools(self):
        @tool(name="check_unread_emails", description="Checks unread emails from Gmail / inbox and lists who sent them and subjects.")
        def check_unread_emails() -> str:
            # Check if IMAP credentials are provided
            user_email = os.getenv("GMAIL_ADDRESS", "")
            app_password = os.getenv("GMAIL_APP_PASSWORD", "")

            try:
                import config
                user_email = getattr(config, "gmail_address", user_email)
                app_password = getattr(config, "gmail_app_password", app_password)
            except Exception:
                pass

            if not user_email or not app_password:
                open_url_tab("https://mail.google.com")
                return ("Gmail credentials not set in config.py yet. "
                        "I have opened Gmail in your browser tab. "
                        "To enable automatic AI reading, add your gmail_address and app_password.")

            try:
                mail = imaplib.IMAP4_SSL("imap.gmail.com")
                mail.login(user_email, app_password)
                mail.select("inbox")

                status, messages = mail.search(None, 'UNSEEN')
                mail_ids = messages[0].split()
                if not mail_ids:
                    return "You have no unread emails in your inbox, sir."

                results = []
                # Read top 3 unread emails
                for i in mail_ids[-3:]:
                    res, msg_data = mail.fetch(i, '(RFC822)')
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            subject, encoding = decode_header(msg["Subject"])[0]
                            if isinstance(subject, bytes):
                                subject = subject.decode(encoding or "utf-8", errors="ignore")
                            from_ = msg.get("From", "Unknown")
                            results.append(f"From {from_}: '{subject}'")

                mail.close()
                mail.logout()
                return f"You have {len(mail_ids)} unread emails. Recent ones: " + "; ".join(results)
            except Exception as e:
                return f"Failed to check emails: {e}"

        @tool(name="draft_or_send_email", description="Opens Gmail draft or sends an email to a recipient.")
        def draft_or_send_email(to_email: str, subject: str, body: str) -> str:
            import urllib.parse
            encoded_subject = urllib.parse.quote(subject)
            encoded_body = urllib.parse.quote(body)
            compose_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={to_email}&su={encoded_subject}&body={encoded_body}"
            open_url_tab(compose_url)
            return f"Opened Gmail draft to {to_email} with subject '{subject}'."

# Auto-instantiate and register tools
mail_plugin = MailPlugin()
mail_plugin.register_tools()
