#!/usr/bin/env python3
"""R8 Phase-B batch: isolated reproduction of archived synthetic technical checks.

Usage:
  python R8_phase_b_sammelaudit.py --preflight
  python R8_phase_b_sammelaudit.py --run --output-root ~/QuantResearch/R8_Batch

Only two existing audited suites are executed. Null-/power-calibration is deliberately
marked NOT_RUN; never report this script as an overall statistical clearance.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

FILES = {
    'correlation': 'R8_phase_b_korrelations_audit.py',
    'forecast_e2e': 'R8_phase_b_synthetischer_e2e_test.py',
}
RESULTS = {
    'correlation': 'R8_phase_b_korrelations_resultat.json',
    'forecast_e2e': 'R8_phase_b_synthetischer_e2e_resultat.json',
}
DEFAULT_REPO = Path.home() / 'QuantResearch-Git'


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def locate(repo: Path) -> dict[str, Path]:
    root = repo / 'studies' / 'R8_synthetic'
    found = {name: root / file for name, file in FILES.items()}
    missing = [str(p) for p in found.values() if not p.is_file()]
    if missing:
        raise RuntimeError('Prüfdatei fehlt: ' + ', '.join(missing))
    return found


def execute(name: str, source: Path, dest: Path):
    import shutil
    src = dest / source.name
    shutil.copy2(source, src)  # Only copy; never execute inside Git repo.
    result = dest / RESULTS[name]
    command = [sys.executable, str(src)]
    if name == 'forecast_e2e':
        command.append(str(result))
    with (dest / f'{name}.stdout.txt').open('w') as stdout, \
         (dest / f'{name}.stderr.txt').open('w') as stderr:
        proc = subprocess.run(command, cwd=dest, stdout=stdout, stderr=stderr,
                              check=False, timeout=1200, env=os.environ.copy())
    if proc.returncode != 0:
        return {'status': 'FAIL', 'exit_code': proc.returncode,
                'stderr_log': str(dest / f'{name}.stderr.txt')}
    if not result.is_file():
        return {'status': 'FAIL', 'error': 'Ergebnisdatei fehlt'}
    data = json.loads(result.read_text(encoding='utf8'))
    if name == 'correlation':
        passed = (data.get('checks_passed') == 18 and
                  data.get('status') == 'SYNTHETIC_TECH_AUDIT_ONLY' and
                  set(data.get('pairs', {})) == {'BTC_ETH', 'BTC_SOL', 'ETH_SOL'} and
                  data.get('no_real_market_data') is True and
                  data.get('no_phase_c_release') is True)
    else:
        passed = (data.get('status') == 'SYNTHETIC_ONLY_NO_MARKET_MEASUREMENT' and
                  data.get('all_predictions') == 26204 and
                  data.get('zero_future_returns') == 270 and
                  data.get('null_calibration_performed') is False and
                  data.get('market_test_approved') is False and
                  len(data.get('refits', [])) == 3)
    return {'status': 'PASS' if passed else 'FAIL', 'output': str(result),
            'result_sha256': sha256(result), 'contract_valid': bool(passed)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--preflight', action='store_true')
    mode.add_argument('--run', action='store_true')
    parser.add_argument('--repo', type=Path, default=DEFAULT_REPO)
    parser.add_argument('--output-root', type=Path, default=Path.home()/'QuantResearch'/'R8_Batch')
    a = parser.parse_args()
    sources = locate(a.repo)
    hashes = {key: sha256(path) for key, path in sources.items()}
    print('Quelle (nur lesend):', a.repo / 'studies/R8_synthetic')
    print('Quellprüfsummen:', json.dumps(hashes, indent=2))
    if a.preflight:
        for pkg in ['numpy','pandas','scipy','sklearn']:
            __import__(pkg)
        print('PREFLIGHT: PASS. Kein Test ausgeführt.')
        return
    root = a.output_root.expanduser().resolve()
    # Ensure destination is not inside the repo, including symlink-based overlap.
    repo = a.repo.expanduser().resolve()
    if root == repo or repo in root.parents or root in repo.parents:
        raise RuntimeError('Ausgabe muss außerhalb des Git-Repositories liegen')
    root.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='R8_phase_b_', dir=root))
    summary = {'status': 'PHASE_B_TECHNICAL_REPRODUCTION_ONLY',
               'created_utc': datetime.now(timezone.utc).isoformat(),
               'source_sha256': hashes, 'workdir': str(work),
               'suites': {},
               'null_false_positive_calibration': 'NOT_RUN',
               'weak_effect_power_calibration': 'NOT_RUN',
               'phase_c_release': False,
               'no_market_data_used': True}
    for name, source in sources.items():
        print('Starte synthetische Suite:', name, flush=True)
        try:
            summary['suites'][name] = execute(name, source, work)
        except (Exception, subprocess.TimeoutExpired) as e:
            summary['suites'][name] = {'status': 'FAIL', 'error': str(e)}
    if any(item['status'] != 'PASS' for item in summary['suites'].values()):
        summary['status'] = 'TECHNICAL_REPRODUCTION_FAILED'
    output = work / 'R8_Batch_Result.json'
    output.write_text(json.dumps(summary, indent=2, ensure_ascii=False)+'\n', encoding='utf8')
    print('Ergebnisse:', output)
    print('Teiltests:', {k:v['status'] for k,v in summary['suites'].items()})
    print('Statistische Null-/Power-Kalibrierung: NICHT AUSGEFÜHRT')
    print('Phase-C-Freigabe: NEIN')
    if summary['status'] == 'TECHNICAL_REPRODUCTION_FAILED':
        sys.exit(1)


if __name__ == '__main__':
    main()
