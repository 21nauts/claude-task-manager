#!/usr/bin/env python3
"""
Sync Manager for Claude Task Manager
Handles automatic Git sync with configurable intervals
"""

import subprocess
import threading
import time
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyncManager:
    """Manages automatic Git synchronization"""

    def __init__(self, repo_path: Path, remote_url: str = None, interval_minutes: int = 120):
        """
        Initialize sync manager

        Args:
            repo_path: Path to the Git repository
            remote_url: Remote Git URL (optional)
            interval_minutes: Sync interval in minutes (default: 2 hours)
        """
        self.repo_path = Path(repo_path).expanduser()
        self.remote_url = remote_url
        self.interval_minutes = interval_minutes
        self.interval_seconds = interval_minutes * 60
        self._sync_thread = None
        self._stop_flag = False
        self._last_sync = None

    def setup_remote(self, remote_url: str):
        """Set up Git remote for the repository"""
        try:
            # Remove existing origin if any
            subprocess.run(
                ["git", "remote", "remove", "origin"],
                cwd=self.repo_path,
                capture_output=True
            )
        except:
            pass

        # Add new origin
        try:
            subprocess.run(
                ["git", "remote", "add", "origin", remote_url],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            self.remote_url = remote_url
            logger.info(f"✅ Remote configured: {remote_url}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to setup remote: {e}")
            return False

    def clone_or_init(self):
        """Clone repository if it doesn't exist, or initialize if needed"""
        if self.repo_path.exists():
            git_dir = self.repo_path / ".git"
            if git_dir.exists():
                logger.info(f"✅ Repository exists at {self.repo_path}")
                return True
            else:
                logger.info(f"⚠️  Directory exists but not a Git repo, initializing...")
                return self._init_repo()
        else:
            if self.remote_url:
                logger.info(f"📥 Cloning from {self.remote_url}...")
                return self._clone_repo()
            else:
                logger.info(f"🆕 Creating new repository...")
                return self._init_repo()

    def _clone_repo(self) -> bool:
        """Clone repository from remote"""
        try:
            subprocess.run(
                ["git", "clone", self.remote_url, str(self.repo_path)],
                check=True,
                capture_output=True
            )
            logger.info(f"✅ Cloned repository to {self.repo_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Clone failed: {e}")
            # Fall back to init
            return self._init_repo()

    def _init_repo(self) -> bool:
        """Initialize new Git repository"""
        try:
            self.repo_path.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "init"],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )

            # Create basic structure
            (self.repo_path / "tasks").mkdir(exist_ok=True)
            (self.repo_path / "projects").mkdir(exist_ok=True)

            # Create .gitignore
            gitignore = self.repo_path / ".gitignore"
            gitignore.write_text("*.pyc\n__pycache__/\n.DS_Store\n")

            # Initial commit
            subprocess.run(
                ["git", "add", "."],
                cwd=self.repo_path,
                check=True
            )
            subprocess.run(
                ["git", "commit", "-m", "Initial commit: Claude tasks repository"],
                cwd=self.repo_path,
                capture_output=True
            )

            logger.info(f"✅ Initialized repository at {self.repo_path}")

            # Set up remote if provided
            if self.remote_url:
                self.setup_remote(self.remote_url)

            return True
        except Exception as e:
            logger.error(f"❌ Init failed: {e}")
            return False

    def sync_now(self, push: bool = True) -> bool:
        """
        Perform immediate sync (pull + optional push)

        Args:
            push: Whether to push changes after pull

        Returns:
            True if sync succeeded
        """
        if not self.remote_url:
            logger.warning("⚠️  No remote configured, skipping sync")
            return False

        try:
            # Pull first
            logger.info("📥 Pulling latest changes...")
            result = subprocess.run(
                ["git", "pull", "--rebase"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.warning(f"⚠️  Pull had issues: {result.stderr}")

            # Push if requested and there are changes
            if push:
                # Check if there are commits to push
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True
                )

                # Commit any uncommitted changes first
                if result.stdout.strip():
                    logger.info("📝 Committing pending changes...")
                    subprocess.run(
                        ["git", "add", "."],
                        cwd=self.repo_path,
                        check=True
                    )
                    subprocess.run(
                        ["git", "commit", "-m", f"Auto-sync: {datetime.now().isoformat()}"],
                        cwd=self.repo_path,
                        capture_output=True
                    )

                logger.info("📤 Pushing changes...")
                result = subprocess.run(
                    ["git", "push"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    logger.warning(f"⚠️  Push had issues: {result.stderr}")

            self._last_sync = datetime.now()
            logger.info(f"✅ Sync completed at {self._last_sync.strftime('%H:%M:%S')}")
            return True

        except Exception as e:
            logger.error(f"❌ Sync failed: {e}")
            return False

    def start_auto_sync(self):
        """Start automatic sync background thread"""
        if self._sync_thread and self._sync_thread.is_alive():
            logger.warning("⚠️  Auto-sync already running")
            return

        self._stop_flag = False
        self._sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._sync_thread.start()
        logger.info(f"🔄 Auto-sync started (interval: {self.interval_minutes} minutes)")

    def stop_auto_sync(self):
        """Stop automatic sync"""
        self._stop_flag = True
        if self._sync_thread:
            self._sync_thread.join(timeout=5)
        logger.info("🛑 Auto-sync stopped")

    def _sync_loop(self):
        """Background sync loop"""
        while not self._stop_flag:
            try:
                self.sync_now()
            except Exception as e:
                logger.error(f"❌ Auto-sync error: {e}")

            # Sleep in 10-second intervals to allow quick stopping
            for _ in range(int(self.interval_seconds / 10)):
                if self._stop_flag:
                    break
                time.sleep(10)

    def get_status(self) -> dict:
        """Get sync status"""
        return {
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "interval_minutes": self.interval_minutes,
            "remote_url": self.remote_url,
            "is_running": self._sync_thread and self._sync_thread.is_alive()
        }


if __name__ == "__main__":
    # Test sync manager
    sync = SyncManager(
        repo_path=Path.home() / "claude-tasks",
        interval_minutes=1  # 1 minute for testing
    )

    print(f"✅ Sync manager initialized")
    print(f"✅ Repository: {sync.repo_path}")
    print(f"✅ Interval: {sync.interval_minutes} minutes")

    # Test clone or init
    sync.clone_or_init()

    # Test status
    status = sync.get_status()
    print(f"✅ Status: {status}")
