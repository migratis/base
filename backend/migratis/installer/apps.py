import json
import shutil
from pathlib import Path
from django.apps import AppConfig


class InstallerConfig(AppConfig):
    name = 'migratis.installer'
    label = 'installer'
    verbose_name = 'Installer'

    def ready(self):
        """
        1. Fix any broken migration imports written by a bad codegen before
           Django's migration loader tries to import them.
        2. Apply any pending install (migrate + seed) that was deferred from
           the install endpoint because StatReloader killed the request handler
           before the subprocesses could run.
        """
        try:
            backend_root = Path(__file__).resolve().parent.parent.parent

            # ── Fix broken migration imports ───────────────────────────────
            for migrations_dir in backend_root.glob('*/migrations'):
                for mig in migrations_dir.glob('*.py'):
                    try:
                        txt = mig.read_text()
                        if 'backend.' in txt:
                            mig.write_text(txt.replace('backend.', ''))
                            pycache = migrations_dir / '__pycache__'
                            if pycache.exists():
                                shutil.rmtree(pycache, ignore_errors=True)
                    except OSError:
                        pass

            # ── Apply pending install ──────────────────────────────────────
            pending = backend_root / 'settings_patches' / '_pending_install.json'
            if pending.exists():
                try:
                    from django.core.management import call_command
                    data = json.loads(pending.read_text())
                    module = data.get('module', '')
                    call_command('migrate', '--run-syncdb', verbosity=1)
                    if module:
                        try:
                            call_command(f'seed_{module}', verbosity=1)
                        except Exception:
                            pass  # seed command optional
                    pending.unlink()  # only removed on success
                except Exception:
                    pass  # never crash Django startup; file stays → retries next restart

        except Exception:
            pass
