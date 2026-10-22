"""Server-side rendering of notification templates."""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "packages" / "notification-templates"

_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=select_autoescape(["html"]))


def render(template_name, variables):
    return _env.get_template(template_name).render(**variables)
