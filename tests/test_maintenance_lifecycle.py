"""A stopped maintenance worker must never turn into a backup/prune busy loop."""

import asyncio
import threading

import pytest

import primer.server as srv


def test_shutdown_during_a_pass_exits_without_another_pass(monkeypatch):
    entered, release, shutdown = threading.Event(), threading.Event(), threading.Event()
    calls = []
    bound_store = object()

    def run(store, directory):
        calls.append((store, directory))
        entered.set()
        assert release.wait(2)

    monkeypatch.setattr(srv, '_run_maintenance_once', run)
    worker = threading.Thread(target=srv._maintenance_loop,
                              args=(shutdown, bound_store, '/unused-test-backups'), daemon=True)
    worker.start()
    try:
        assert entered.wait(1)
        shutdown.set()
    finally:
        release.set()
        worker.join(1)
    assert not worker.is_alive()
    assert calls == [(bound_store, '/unused-test-backups')]


def test_already_stopped_worker_does_no_database_work(monkeypatch):
    shutdown = threading.Event()
    shutdown.set()
    monkeypatch.setattr(srv, '_run_maintenance_once', lambda *_args: pytest.fail('Unexpected maintenance'))
    srv._maintenance_loop(shutdown, object(), '/unused-test-backups')


def test_each_lifespan_owns_and_stops_its_worker_even_on_error(monkeypatch, tmp_path):
    entered = threading.Event()
    calls = []
    bound_store = object()
    monkeypatch.setattr(srv, 'learner', bound_store)
    monkeypatch.setattr(srv, 'BACKUP_DIR', str(tmp_path))
    monkeypatch.setattr(srv, 'backup_status', lambda: {'mode': 'managed_remote', 'advice': 'test'})

    def loop(shutdown, store, directory):
        calls.append((shutdown, store, directory, threading.current_thread()))
        entered.set()
        assert shutdown.wait(2)

    monkeypatch.setattr(srv, '_maintenance_loop', loop)

    async def exercise():
        for failing in (False, True, False):
            entered.clear()
            try:
                async with srv._lifespan(None):
                    assert await asyncio.to_thread(entered.wait, 1)
                    if failing:
                        raise ValueError('simulated request failure')
            except ValueError:
                assert failing
            assert calls[-1][0].is_set()
            assert not calls[-1][3].is_alive()

    asyncio.run(exercise())
    assert len(calls) == 3
    assert len({id(call[0]) for call in calls}) == 3
    assert all(call[1] is bound_store and call[2] == str(tmp_path) for call in calls)
