from .auth_routes import auth_bp
from .user_routes import user_bp
from .hierarchy_routes import hierarchy_bp
from .report_routes import report_bp
from .enem import enem_bp
from .paaeb import paaeb_bp
from .school_routes import bp as school_bp

__all__ = ["auth_bp", "user_bp", "hierarchy_bp", "report_bp", "enem_bp", "paaeb_bp", "school_bp"]
