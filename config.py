#!/usr/bin/env python3
"""
Configuration Management for Claude Task Manager
Handles user settings and repository configuration
"""

import json
from pathlib import Path
from typing import Optional


class TaskManagerConfig:
    """Manages task manager configuration"""

    def __init__(self, config_dir: Path = None):
        """Initialize configuration manager"""
        if config_dir:
            self.config_dir = Path(config_dir).expanduser()
        else:
            self.config_dir = Path.home() / ".config" / "claude-task-manager"

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                return json.loads(self.config_file.read_text())
            except:
                return self._default_config()
        return self._default_config()

    def _default_config(self) -> dict:
        """Return default configuration"""
        return {
            "tasks_repo_path": str(Path.home() / "claude-tasks"),
            "tasks_repo_remote": None,  # User will set this
            "auto_sync_enabled": True,
            "auto_sync_interval_minutes": 120,  # 2 hours
            "auto_push_on_change": True,
            "sync_on_startup": True,
            "version": "2.0.0"
        }

    def save(self):
        """Save configuration to file"""
        self.config_file.write_text(json.dumps(self.config, indent=2))

    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)

    def set(self, key: str, value):
        """Set configuration value"""
        self.config[key] = value
        self.save()

    def is_configured(self) -> bool:
        """Check if initial setup is complete"""
        return self.config.get("tasks_repo_remote") is not None

    def get_tasks_repo_path(self) -> Path:
        """Get tasks repository path"""
        return Path(self.config["tasks_repo_path"]).expanduser()

    def get_tasks_repo_remote(self) -> Optional[str]:
        """Get tasks repository remote URL"""
        return self.config.get("tasks_repo_remote")

    def setup_initial_config(self, remote_url: str, local_path: str = None):
        """
        Initial setup wizard configuration

        Args:
            remote_url: Git remote URL for tasks repository
            local_path: Optional local path (defaults to ~/claude-tasks)
        """
        if local_path:
            self.config["tasks_repo_path"] = local_path

        self.config["tasks_repo_remote"] = remote_url
        self.save()

        return {
            "tasks_repo_path": self.get_tasks_repo_path(),
            "tasks_repo_remote": remote_url
        }


# Singleton instance
_config_instance = None


def get_config() -> TaskManagerConfig:
    """Get configuration singleton"""
    global _config_instance
    if _config_instance is None:
        _config_instance = TaskManagerConfig()
    return _config_instance


if __name__ == "__main__":
    # Test configuration
    config = TaskManagerConfig()
    print(f"✅ Config directory: {config.config_dir}")
    print(f"✅ Config file: {config.config_file}")
    print(f"✅ Tasks repo path: {config.get_tasks_repo_path()}")
    print(f"✅ Is configured: {config.is_configured()}")
    print(f"✅ Auto-sync enabled: {config.get('auto_sync_enabled')}")
    print(f"✅ Sync interval: {config.get('auto_sync_interval_minutes')} minutes")
