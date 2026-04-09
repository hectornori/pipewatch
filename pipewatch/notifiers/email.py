import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from pipewatch.config import EmailConfig

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Sends pipeline failure alerts via SMTP email."""

    def __init__(self, config: EmailConfig):
        self.config = config

    def send(self, pipeline_name: str, message: str, error: Optional[str] = None) -> bool:
        """Send an email notification for a pipeline failure.

        Returns True if the email was sent successfully, False otherwise.
        """
        subject = f"[pipewatch] Pipeline failure: {pipeline_name}"
        body = self._build_body(pipeline_name, message, error)
        msg = self._build_message(subject, body)
        try:
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=15) as server:
                if self.config.use_tls:
                    server.starttls()
                if self.config.username and self.config.password:
                    server.login(self.config.username, self.config.password)
                server.sendmail(
                    self.config.from_address,
                    self.config.to_addresses,
                    msg.as_string(),
                )
            logger.info("Email notification sent for pipeline '%s'.", pipeline_name)
            return True
        except (smtplib.SMTPException, OSError) as exc:
            logger.error("Failed to send email notification: %s", exc)
            return False

    def _build_body(self, pipeline_name: str, message: str, error: Optional[str]) -> str:
        body = f"Pipeline failure detected: {pipeline_name}\n\n{message}"
        if error:
            body += f"\n\nError details:\n{error}"
        return body

    def _build_message(self, subject: str, body: str) -> MIMEMultipart:
        msg = MIMEMultipart()
        msg["From"] = self.config.from_address
        msg["To"] = ", ".join(self.config.to_addresses)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        return msg
