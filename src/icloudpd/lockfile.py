"""Lockfile management to prevent parallel execution for the same user credentials."""

import fcntl
import hashlib
import os
from contextlib import contextmanager
from logging import Logger
from pathlib import Path
from typing import Generator


def get_lockfile_path(username: str, cookie_directory: str | None) -> Path:
    """Generate a lockfile path based on username.
    
    The lockfile is placed in the cookie directory (if specified) or /tmp.
    The filename is based on a hash of the username for privacy.
    
    Args:
        username: The iCloud username/email
        cookie_directory: Directory where cookies are stored, or None for /tmp
        
    Returns:
        Path to the lockfile
    """
    # Create a hash of the username for the lockfile name
    username_hash = hashlib.md5(username.encode()).hexdigest()[:12]
    lockfile_name = f".icloudpd_{username_hash}.lock"
    
    if cookie_directory:
        return Path(cookie_directory) / lockfile_name
    else:
        return Path("/tmp") / lockfile_name


class LockfileError(Exception):
    """Raised when unable to acquire lockfile (another instance is running)."""
    pass


@contextmanager
def acquire_lock(
    username: str,
    cookie_directory: str | None,
    logger: Logger,
) -> Generator[Path, None, None]:
    """Context manager to acquire an exclusive lock for a user.
    
    Uses flock() for proper file locking that automatically releases
    when the process exits (even on crash).
    
    Args:
        username: The iCloud username/email
        cookie_directory: Directory where cookies are stored
        logger: Logger instance
        
    Yields:
        Path to the lockfile
        
    Raises:
        LockfileError: If another instance is already running for this user
    """
    lockfile_path = get_lockfile_path(username, cookie_directory)
    
    # Ensure parent directory exists
    lockfile_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Open (or create) the lockfile
    lock_fd = open(lockfile_path, 'w')
    
    try:
        # Try to acquire exclusive lock (non-blocking)
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        
        # Write PID to lockfile for debugging
        lock_fd.write(f"{os.getpid()}\n")
        lock_fd.flush()
        
        logger.debug(f"Acquired lock for user {username} at {lockfile_path}")
        
        yield lockfile_path
        
    except BlockingIOError:
        lock_fd.close()
        # Try to read the PID of the blocking process
        try:
            with open(lockfile_path, 'r') as f:
                blocking_pid = f.read().strip()
            logger.error(
                f"Another instance is already running for user {username} "
                f"(PID: {blocking_pid}). Skipping this run."
            )
        except Exception:
            logger.error(
                f"Another instance is already running for user {username}. "
                f"Skipping this run."
            )
        raise LockfileError(f"Cannot acquire lock for {username}")
        
    finally:
        # Release lock and close file
        try:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            lock_fd.close()
        except Exception:
            pass  # Ignore errors during cleanup
