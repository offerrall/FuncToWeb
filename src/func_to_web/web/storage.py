"""The two storages of the process and what they have in common.

Uploads and returned files are kept in two directories that differ in what a
name means and in what a sweep may delete, and those differences live with
each of them: upload.py, returned_files.py and the two rules of pending.py.
What they share is here, written once: a directory and a TTL settled by the
first router that asks, one sweeper thread for both, and the partial file
every write goes through before its name is published.
"""

import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from random import uniform
from threading import Lock, Thread
from time import sleep
from uuid import uuid4
from warnings import warn

from func_to_web.config import RETURNS_DIR, UPLOADS_DIR
from func_to_web.web import pending
from func_to_web.web.pending import PART_SUFFIX, discard

DEFAULT_TTL: int = 60 * 60

PUBLISH_ATTEMPTS: int = 5

PUBLISH_PAUSE: float = 0.01

SWEEP_MIN_SECONDS: float = 30 * 60

SWEEP_MAX_SECONDS: float = 60 * 60

SWEEPER_NAME: str = "func-to-web-storage-sweeper"

# The sweeper is one per process, not one per router and not one per
# directory: several spaces mounted together must not each start a thread.
# The same lock guards what each storage settles, so a policy and the thread
# that enforces it are decided together.
_settling: Lock = Lock()

_sweeper: Thread | None = None


@dataclass(frozen=True)
class Policy:
    """Where a storage keeps its files and how long the unclaimed ones last."""

    directory: Path
    ttl: int | None


class Storage:
    """One storage of the process: a policy settled once, and its sweep.

    One process is one directory per storage, so where the files go and how
    long they last are settled together by the first router that gets here,
    for the thread and for every resolver. Until then the policy is the
    default one, which is what whoever never builds a router reads.

    `rule` is what tells the storages apart when sweeping: which names of the
    directory are this storage's to delete once the TTL has passed.
    """

    def __init__(
        self,
        directory_name: str,
        ttl_name: str,
        directory: Path,
        rule: Callable[[Path, int], None],
    ) -> None:
        self._directory_name = directory_name
        self._ttl_name = ttl_name
        self._rule = rule
        self._policy = Policy(directory, DEFAULT_TTL)
        self._adopted = False

    @property
    def directory(self) -> Path:
        return self._policy.directory

    @property
    def ttl(self) -> int | None:
        return self._policy.ttl

    def adopt(self, directory: Path, ttl: int | None) -> None:
        """Settle the policy, sweep now and start the sweeper if needed.

        A later router asking for either half differently is told that it
        was not applied. The sweep is synchronous as well as threaded because
        a short-lived process may exit before the thread wakes.
        """
        with _settling:
            if not self._adopted:
                self._policy = Policy(directory, ttl)
                self._adopted = True

            settled = self._policy

            _start_sweeper(settled.ttl is not None)

        if directory != settled.directory:
            _ignored(self._directory_name, directory, settled.directory)

        if ttl != settled.ttl:
            _ignored(self._ttl_name, ttl, settled.ttl)

        self.sweep()

    def sweep(self) -> None:
        """One sweep of the directory with the effective TTL."""
        policy = self._policy

        if policy.ttl is None:
            return

        self._rule(policy.directory, policy.ttl)


UPLOADS: Storage = Storage("uploads_dir", "pending_ttl", UPLOADS_DIR,
                           pending.sweep)

RETURNS: Storage = Storage("returns_dir", "returns_ttl", RETURNS_DIR,
                           pending.sweep_returns)


@contextmanager
def partial_in(directory: Path, name: str) -> Iterator[Path]:
    """A partial file to write `name` through, gone if the write fails.

    Nothing is ever written under the name a reader looks for: the bytes land
    here and publish() renames them once they are whole. Leaving the block
    with an error deletes the partial, and deleting it never masks the error
    that got there first.
    """
    partial = directory / f"{name}.{uuid4().hex}{PART_SUFFIX}"

    directory.mkdir(parents=True, exist_ok=True)

    try:
        yield partial
    except BaseException:
        discard(partial)

        raise


def publish(partial: Path, target: Path) -> None:
    """Rename a whole partial file onto its name, atomically.

    Retried a few times: Windows refuses a rename while anything else holds
    either name open, and that passes.
    """
    for remaining in reversed(range(PUBLISH_ATTEMPTS)):
        try:
            os.replace(partial, target)
            return
        except OSError:
            if not remaining:
                raise

            sleep(PUBLISH_PAUSE)


def _start_sweeper(needed: bool) -> None:
    global _sweeper

    if needed and _sweeper is None:
        _sweeper = Thread(target=_sweeping, name=SWEEPER_NAME, daemon=True)
        _sweeper.start()


def _ignored(name: str, asked: object, settled: object) -> None:
    """Say that a setting arrived after the process had already settled it.

    One piece of prose for every storage setting: only the name and the two
    values change, so whatever else becomes a policy of the process reads the
    same way here.
    """
    warn(
        f"{name}={asked!r} is ignored: this process already stores its files "
        f"with {name}={settled!r}, settled by an earlier router. Storage is "
        f"one policy per process, not one per router.",
        stacklevel=4,
    )


def _sweeping() -> None:
    while True:
        for storage in (UPLOADS, RETURNS):
            try:
                storage.sweep()
            except Exception:
                # A failed pass is never the end of the thread: whatever it
                # was, the next cycle finds the same directory and tries
                # again.
                continue

        # Drawn again every cycle: workers that started together must drift
        # apart instead of sweeping in lockstep forever.
        sleep(uniform(SWEEP_MIN_SECONDS, SWEEP_MAX_SECONDS))
