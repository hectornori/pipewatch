"""Notifier sub-package for pipewatch."""
from pipewatch.notifiers.slack import SlackNotifier
from pipewatch.notifiers.email import EmailNotifier
from pipewatch.notifiers.template_notifier import TemplateNotifier, template_notifier_from_config

__all__ = [
    "SlackNotifier",
    "EmailNotifier",
    "TemplateNotifier",
    "template_notifier_from_config",
]
