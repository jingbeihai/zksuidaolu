"""共享 Jinja2 模板实例"""
from fastapi.templating import Jinja2Templates
import settings

templates = Jinja2Templates(directory="templates")
templates.env.globals["app_title"] = settings.APP_TITLE
templates.env.globals["static_version"] = settings.STATIC_VERSION
