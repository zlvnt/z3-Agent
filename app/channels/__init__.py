"""
Channel package for multi-channel.
"""

from .base import BaseChannel

# Channel registry for dynamic channel management
AVAILABLE_CHANNELS = {
    "telegram": "app.channels.telegram.handler.TelegramChannel",
    # Future channels will be added here
}

def get_channel_class(channel_name: str):
    if channel_name not in AVAILABLE_CHANNELS:
        return None
    
    module_path = AVAILABLE_CHANNELS[channel_name]
    module_name, class_name = module_path.rsplit(".", 1)
    
    try:
        import importlib
        module = importlib.import_module(module_name)
        return getattr(module, class_name)
    except (ImportError, AttributeError):
        return None

__all__ = ["BaseChannel", "AVAILABLE_CHANNELS", "get_channel_class"]