#!/usr/bin/env python3
"""Release branch policy, immutable shipping inventory and retryable notices."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
REPO = os.environ.get('GITHUB_REPOSITORY', 'Razdva122/clean-your-tv-lg-webos')
BRANCH = 'release/next'
PLAN = 'release-plan.json'
BUILD_JOBS = {
    'android',
    'build (windows-latest, cytv-windows-x64, dist/cytv.exe)',
    'build (ubuntu-22.04, cytv-linux-x64, dist/cytv)',
    'build (macos-15, cytv-macos-arm64, dist/cytv)',
    'build (macos-15-intel, cytv-macos-x64, dist/cytv)',
}


def parse_version(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{1,4}\.\d{1,4}\.\d{1,4}', value):
        raise ValueError('Expected a final X.Y.Z version')
    return tuple(map(int, value.split('.')))


def number(value):
    if type(value) is not int or value <= 0:
        raise ValueError('PR/issue numbers must be positive integers')
    return value


def validate_shape(plan):
    if type(plan.get('schema')) is not int or plan['schema'] != 1 or not isinstance(plan.get('changes'), list) or not isinstance(plan.get('excluded'), list):
        raise ValueError('Invalid release inventory schema')
    if plan.get('version') is not None:
        parse_version(plan['version'])
    seen = set()
    for key, text in [('changes', 'summary'), ('excluded', 'reason')]:
        for entry in plan[key]:
            pr = number(entry['pr'])
            if pr in seen or not isinstance(entry.get(text), str) or not entry[text].strip():
                raise ValueError('Duplicate PR or missing release inventory description')
            seen.add(pr)
            if key == 'changes':
                issues = entry.get('issues')
                if not isinstance(issues, list) or len(set(map(number, issues))) != len(issues):
                    raise ValueError('Invalid or duplicate issues')
    return seen


def validate_plan(plan, *, branch, same_repo, final, version: str,
                  previous_version, merged_prs, commits, notes):
    listed = validate_shape(plan)
    if final:
        if branch != BRANCH or not same_repo:
            raise ValueError('main accepts only same-repository release/next PRs')
        if plan.get('version') != version or parse_version(version) <= parse_version(previous_version):
            raise ValueError('Finalize the release version and bump release-versions.json')
        if not isinstance(plan.get('acceptance'), str) or not plan['acceptance'].strip() or not notes.strip():
            raise ValueError('Release notes and hardware acceptance evidence are required')
    expected = {p['number'] for p in merged_prs if p.get('merged_at') and p['merge_commit_sha'] in commits}
    if listed != expected:
        raise ValueError(f'Release inventory mismatch: missing={sorted(expected-listed)}, unexpected={sorted(listed-expected)}')


def api(path, *, method='GET', data=None, pages=False):
    args = ['gh', 'api', '--method', method, 'repos/' + REPO + ('/' + path if path else '')]
    if pages:
        args += ['--paginate', '--slurp']
    if data is not None:
        args += ['--input', '-']
    result = json.loads(subprocess.check_output(args, input=json.dumps(data).encode() if data is not None else None))
    return [item for page in result for item in page] if pages else result


def git(*args, root=ROOT):
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()


def read_at(commit, path, root=ROOT):
    if not re.fullmatch('[a-f0-9]{40}', commit):
        raise ValueError('Invalid source SHA')
    return git('show', commit + ':' + path, root=root)


def merged_scope(base, head, root=ROOT):
    commits = set(git('rev-list', base + '..' + head, root=root).splitlines())
    prs = api('pulls?state=closed&base=release%2Fnext&per_page=100', pages=True)
    return commits, prs


def related_issues(body):
    body = re.sub(r'<!--.*?-->', '', body or '', flags=re.S)
    return {int(n) for line in body.splitlines()
            if re.match(r'^Related issues:\s*', line, re.I)
            for n in re.findall(r'(?<![\w/])#([1-9]\d*)\b', line)}


def linked_issues(pr):
    owner, repo = REPO.split('/')
    result = related_issues(api('pulls/' + str(pr)).get('body'))
    cursor = None
    while True:
        query = 'query($owner:String!, $repo:String!, $number:Int!, $cursor:String) {\n          repository(owner:$owner, name:$repo) { pullRequest(number:$number) {\n            closingIssuesReferences(first:100, after:$cursor) {\n              nodes { number repository { nameWithOwner } }\n              pageInfo { hasNextPage endCursor }\n            }\n          } }\n        }'
        args = ['gh', 'api', 'graphql', '-f', 'query=' + query, '-f', 'owner=' + owner,
                '-f', 'repo=' + repo, '-F', 'number=' + str(pr)]
        if cursor:
            args += ['-f', 'cursor=' + cursor]
        response = json.loads(subprocess.check_output(args))
        if response.get('errors'):
            raise ValueError('Cannot resolve linked issues')
        connection = response['data']['repository']['pullRequest']['closingIssuesReferences']
        for issue in connection['nodes']:
            if issue['repository']['nameWithOwner'] != REPO:
                raise ValueError('Cross-repository issue links require explicit separate release tracking')
            result.add(issue['number'])
        if not connection['pageInfo']['hasNextPage']:
            return result
        cursor = connection['pageInfo']['endCursor']


def validate_issues(plan, check_links=False):
    if check_links:
        for change in plan['changes']:
            missing = linked_issues(change['pr']) - set(change['issues'])
            if missing:
                raise ValueError(f"PR #{change['pr']} is missing linked issues in release-plan.json: {sorted(missing)}")
    for issue in sorted({n for change in plan['changes'] for n in change['issues']}):
        if 'pull_request' in api('issues/' + str(issue)):
            raise ValueError(f'#{issue} is a PR; put it in changes, not issues')


def validate_candidate(pr, root=ROOT, check_links=False):
    base, head = pr['base']['sha'], pr['head']['sha']
    plan = json.loads(read_at(head, PLAN, root))
    versions = json.loads(read_at(head, 'release-versions.json', root))
    old = json.loads(read_at(base, 'release-versions.json', root))
    commits, prs = merged_scope(base, head, root)
    validate_plan(plan, branch=pr['head']['ref'], same_repo=pr['head']['repo']['full_name'] == REPO,
                  final=True, version=versions['release'], previous_version=old['release'],
                  merged_prs=prs, commits=commits,
                  notes=read_at(head, 'docs/RELEASE-' + versions['release'] + '.md', root))
    validate_issues(plan, check_links=check_links)
    return plan


def validate_build_jobs(jobs):
    successful = {j['name'] for j in jobs if j['conclusion'] == 'success'}
    if not BUILD_JOBS <= successful:
        raise ValueError('Missing successful candidate jobs: ' + ', '.join(sorted(BUILD_JOBS - successful)))


def wait_for_build(head):
    # Only trusted pushes to the maintained release branch may use the Android signer.
    deadline = time.monotonic() + 2100
    while time.monotonic() < deadline:
        runs = api('actions/workflows/cytv.yml/runs?branch=release%2Fnext&head_sha=' + head + '&per_page=100')['workflow_runs']
        runs = [r for r in runs if r['event'] == 'push' and r['head_sha'] == head and
                r['head_repository']['full_name'] == REPO]
        if runs:
            run = max(runs, key=lambda r: r['id'])
            if run['status'] == 'completed':
                if run['conclusion'] != 'success':
                    raise ValueError('Release candidate builds failed: ' + run['html_url'])
                jobs = api('actions/runs/' + str(run['id']) + '/jobs?filter=latest&per_page=100')['jobs']
                validate_build_jobs(jobs)
                return
        print('Waiting for complete release/next builds at ' + head, flush=True)
        time.sleep(30)
    raise ValueError('No successful complete candidate build within 35 minutes; rerun the policy check')


def check_pr(event):
    pr = event['pull_request']
    if pr['base']['ref'] == BRANCH:
        print('Feature PR targets release/next; no release version is required')
        return
    if pr['base']['ref'] != 'main':
        raise ValueError('PRs must target release/next; only release PRs target main')
    validate_candidate(pr, check_links=True)
    wait_for_build(pr['head']['sha'])
    print('Final release candidate and complete trusted platform builds verified')


def collect(root=ROOT):
    head = git('rev-parse', 'HEAD', root=root)
    base = git('rev-parse', 'origin/main', root=root)
    commits, prs = merged_scope(base, head, root)
    path = root / PLAN
    plan = json.loads(path.read_text())
    validate_shape(plan)
    old = {c['pr']: c for c in plan['changes']}
    included = sorted((p for p in prs if p.get('merged_at') and p['merge_commit_sha'] in commits),
                      key=lambda p: p['number'])
    expected = {p['number'] for p in included}
    plan['excluded'] = [p for p in plan['excluded'] if p['pr'] in expected]
    excluded = {p['pr'] for p in plan['excluded']}
    plan['changes'] = [
        {'pr': p['number'], 'issues': sorted(linked_issues(p['number']) |
                                            set(old.get(p['number'], {}).get('issues', []))),
         'summary': old.get(p['number'], {}).get('summary', p['title'])}
        for p in included if p['number'] not in excluded]
    path.write_text(json.dumps(plan, indent=2) + '\n')
    print('Collected release scope without selecting or changing the version')


def remote_json(path, ref):
    return json.loads(base64.b64decode(api('contents/' + path + '?ref=' + ref)['content']))


def ensure_candidate():
    owner = REPO.split('/')[0]
    existing = api(f'pulls?state=open&base=main&head={owner}:release%2Fnext&per_page=100')
    if existing:
        print('Release candidate already exists: ' + existing[0]['html_url'])
        return existing[0]
    head = api('commits/release%2Fnext')['sha']
    comparison = api('compare/main...' + head)
    if not comparison['ahead_by']:
        print('No next-cycle changes; no candidate PR needed yet')
        return None
    plan = remote_json(PLAN, head)
    validate_shape(plan)
    versions = remote_json('release-versions.json', head)
    published = api('releases/latest')['tag_name']
    previous = remote_json('release-versions.json', published)
    rows = [('Overall release', 'release'), ('Home', 'home'), ('Home Helper', 'helper'),
            ('cytv installer', 'cytv'), ('Android installer / versionCode', 'android'),
            ('Root edition', 'root'), ('Independent updater', 'updater')]
    body = ['## Release candidate', '',
            f'Unfrozen draft after {published}. Base: `main`; head: `release/next`.',
            f'Initial source: `{head}`. Final version and hardware acceptance are not selected.', '',
            '## Scope', '']
    body += [f"- #{c['pr']}: {c['summary']}" +
             (' (Related issues: ' + ', '.join('#' + str(n) for n in c['issues']) + ')' if c['issues'] else '')
             for c in plan['changes']] or ['No implementation PRs collected yet.']
    body += [f"- Excluded #{c['pr']}: {c['reason']}" for c in plan['excluded']]
    body += ['', '## Component versions', '',
             '| Component | Last published | Currently committed | Proposed/final target | Status |',
             '| --- | --- | --- | --- | --- |']
    for label, key in rows:
        old, current = previous[key], versions[key]
        if key == 'android':
            old += ' / ' + str(previous['android_version_code'])
            current += ' / ' + str(versions['android_version_code'])
        body.append(f'| {label} | {old} | {current} | TBD | Target not selected |')
    body += ['', '## Packaging and validation', '',
             'No new artifact builds or TV acceptance are claimed for this draft. Rebuild requirements,',
             'component bumps, rollback evidence and validation of the exact frozen commit remain pending.',
             'Keep pinned Helper baselines and source/package version checks intact.', '',
             '## Release gates', '',
             '- [ ] Collect all implementation PRs and issues in `release-plan.json`.',
             '- [ ] Maintain this description after every scope/version/validation change.',
             '- [ ] Select final versions, synchronize manifests and write release notes.',
             '- [ ] Record actual TV acceptance, limitations and rollback evidence.',
             '- [ ] Complete required tests, all platform builds and Release policy at the frozen head.']
    pr = api('pulls', method='POST', data={'title': 'Next release candidate',
             'head': BRANCH, 'base': 'main', 'draft': True, 'body': '\n'.join(body) + '\n'})
    print('Created release candidate: ' + pr['html_url'])
    return pr


def start_cycle(tag):
    if not re.fullmatch(r'v\d{1,4}\.\d{1,4}\.\d{1,4}', tag):
        raise ValueError('Invalid release tag')
    release = api('releases/tags/' + tag)
    main = api('commits/main')
    if (release['draft'] or release['prerelease'] or release['tag_name'] != tag or
            api('commits/' + tag)['sha'] != main['sha']):
        raise ValueError('Start the next cycle only after publication of the current main commit')
    subprocess.run(['node', str(ROOT / 'scripts/publish-release.cjs'), tag, '--check-only'], check=True)
    head = api('commits/release%2Fnext')['sha']
    comparison = api('compare/' + main['sha'] + '...' + head)
    if comparison['ahead_by']:
        plan = remote_json(PLAN, head)
        if plan.get('version') is not None:
            raise ValueError('release/next already has newer work; refusing to reset its plan')
        return ensure_candidate()
    plan = {'schema': 1, 'version': None, 'changes': [], 'excluded': [], 'acceptance': ''}
    tree = api('git/trees', method='POST', data={'base_tree': main['commit']['tree']['sha'],
               'tree': [{'path': PLAN, 'mode': '100644', 'type': 'blob',
                         'content': json.dumps(plan, indent=2) + '\n'}]})
    commit = api('git/commits', method='POST', data={
        'message': 'Start next release cycle after verified ' + tag + ' publication',
        'tree': tree['sha'], 'parents': [main['sha']]})
    # A non-fast-forward update fails if another writer has added work meanwhile.
    api('git/refs/heads/' + BRANCH, method='PATCH', data={'sha': commit['sha'], 'force': False})
    return ensure_candidate()


def inventory_at(commit, root=ROOT):
    associated = api('commits/' + commit + '/pulls?per_page=100', pages=True)
    prs = [p for p in associated if p.get('merged_at') and p['merge_commit_sha'] == commit and
           p['base']['ref'] == 'main' and p['head']['ref'] == BRANCH and p['head']['repo']['full_name'] == REPO]
    if len(prs) != 1:
        raise ValueError('Release source must be the exact merge of one release/next PR into main')
    pr = prs[0]
    # GitHub's live base SHA can advance; the merge's first parent is immutable.
    pr['base']['sha'] = git('rev-parse', commit + '^1', root=root)
    plan = validate_candidate(pr, root)
    if json.loads(read_at(commit, PLAN, root)) != plan:
        raise ValueError('Merged release plan differs from the approved candidate')
    return {'schema': 1, 'tag': 'v' + plan['version'], 'source_commit': commit,
            'release_pr': pr['number'], 'changes': plan['changes'], 'excluded': plan['excluded']}


def notification_bodies(inventory, url):
    tag = inventory['tag']
    if not re.fullmatch(r'v\d{1,4}\.\d{1,4}\.\d{1,4}', tag):
        raise ValueError('Invalid notice tag')
    grouped = {}
    for change in inventory['changes']:
        for target in {change['pr'], *change['issues'], inventory['release_pr']}:
            grouped.setdefault(number(target), []).append(change)
    grouped.setdefault(number(inventory['release_pr']), [])
    result = {}
    for target, changes in grouped.items():
        lines = [f'Released in [{tag}]({url}).', '', 'Changes delivered here:']
        lines += [f"- {c['summary']} (PR #{c['pr']})" for c in changes]
        if not changes:
            lines.append('- Release preparation and publication.')
        result[target] = '\n'.join(lines) + f'\n\n<!-- shipped:{tag} -->'
    return result


def existing_notice(comments, tag):
    return next((c for c in comments if c['user']['login'] == 'github-actions[bot]' and
                 c['user']['type'] == 'Bot' and f'<!-- shipped:{tag} -->' in c['body']), None)


def validate_publication(release, inventory, build, commit):
    if (release['draft'] or release['prerelease'] or inventory.get('schema') != 1 or
        release['tag_name'] != inventory['tag'] or build['tag'] != inventory['tag'] or
        inventory['source_commit'] != commit or build['source_commit'] != commit):
        raise ValueError('Notifications require a published stable release at the exact inventory/build/tag commit')


def notify(tag):
    if not re.fullmatch(r'v\d{1,4}\.\d{1,4}\.\d{1,4}', tag):
        raise ValueError('Invalid release tag')
    release = api('releases/tags/' + tag)
    commit = api('commits/' + tag)['sha']
    # Verification is repeated on retries as well as on the publication path.
    subprocess.run(['node', str(ROOT / 'scripts/publish-release.cjs'), tag, '--check-only'], check=True)
    if not any(a['name'] == 'RELEASE-INVENTORY.json' for a in release['assets']):
        tree = api('git/trees/' + commit)['tree']
        if any(item['path'] == PLAN for item in tree):
            raise ValueError('Release inventory is missing from a release using the new flow')
        print('Legacy release predates release inventory; no shipping notices to send')
        return
    with tempfile.TemporaryDirectory() as folder:
        subprocess.run(['gh', 'release', 'download', tag, '--repo', REPO,
                        '--pattern', 'RELEASE-INVENTORY.json', '--pattern', 'BUILD-INFO.json',
                        '--pattern', 'SHA256SUMS', '--dir', folder], check=True)
        directory = Path(folder)
        raw = (directory / 'RELEASE-INVENTORY.json').read_bytes()
        sums = dict(line.split(None, 1)[::-1] for line in (directory / 'SHA256SUMS').read_text().splitlines())
        if sums.get('RELEASE-INVENTORY.json') != hashlib.sha256(raw).hexdigest():
            raise ValueError('Release inventory checksum mismatch')
        inventory = json.loads(raw)
        validate_publication(release, inventory, json.loads((directory / 'BUILD-INFO.json').read_text()), commit)
        if inventory != inventory_at(commit):
            raise ValueError('Published inventory differs from the committed release scope')
    deliver_notices(inventory, release['html_url'])


def deliver_notices(inventory, url):
    tag = inventory['tag']
    failed = []
    for target, body in notification_bodies(inventory, url).items():
        try:
            comments = api(f'issues/{target}/comments?per_page=100', pages=True)
            previous = existing_notice(comments, tag)
            if previous is None:
                api(f'issues/{target}/comments', method='POST', data={'body': body})
            elif previous['body'] != body:
                api('issues/comments/' + str(previous['id']), method='PATCH', data={'body': body})
            print(f'Notified #{target}')
        except subprocess.CalledProcessError:
            failed.append(target)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as summary:
            summary.write(f'Published release {tag}. Notice failures: {failed or "none"}.\n')
    if failed:
        raise ValueError('Retry missing release notices for: ' + ', '.join(map(str, failed)))


def protect():
    # No mandatory second maintainer: this repository can be maintained solo.
    policy = {'required_status_checks': {'strict': True, 'checks': [
        {'context': name, 'app_id': 15368} for name in
        ['Release policy', 'tests (ubuntu-latest)', 'tests (macos-latest)']]},
        'enforce_admins': True, 'required_pull_request_reviews': {
            'required_approving_review_count': 0, 'dismiss_stale_reviews': True,
            'require_code_owner_reviews': False}, 'restrictions': None,
        'allow_force_pushes': False, 'allow_deletions': False,
        'required_conversation_resolution': True}
    # Preserve candidate ancestry across releases. GitHub merge methods are repo-wide.
    api('', method='PATCH', data={'allow_merge_commit': True, 'allow_squash_merge': False,
                                 'allow_rebase_merge': False, 'delete_branch_on_merge': False})
    settings = api('')
    if not settings['allow_merge_commit'] or settings['allow_squash_merge'] or settings['allow_rebase_merge'] or settings['delete_branch_on_merge']:
        raise ValueError('Release flow requires merge commits; repository settings were not applied')
    api('branches/main/protection', method='PUT', data=policy)
    actual = api('branches/main/protection')
    expected = {c['context'] for c in policy['required_status_checks']['checks']}
    if (not actual['enforce_admins']['enabled'] or not actual['required_status_checks']['strict'] or
        {c['context'] for c in actual['required_status_checks']['checks']} != expected or
        actual['allow_force_pushes']['enabled'] or actual['allow_deletions']['enabled'] or
        not actual['required_conversation_resolution']['enabled'] or
        actual.get('required_pull_request_reviews') is None or
        any(c.get('app_id') != 15368 for c in actual['required_status_checks']['checks'])):
        raise ValueError('main protection read-back does not match the requested policy')
    print('Verified main protection: PR + release policy + Linux/macOS tests; admins included')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check', 'collect', 'inventory', 'notify', 'protect',
                                           'ensure-candidate', 'start-cycle'])
    parser.add_argument('--tag')
    parser.add_argument('--source-root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.command == 'check':
        check_pr(json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text()))
    elif args.command == 'collect':
        collect(args.source_root)
    elif args.command == 'ensure-candidate':
        ensure_candidate()
    elif args.command == 'start-cycle':
        if not args.tag:
            parser.error('start-cycle requires --tag')
        start_cycle(args.tag)
    elif args.command == 'inventory':
        if args.output is None:
            parser.error('inventory requires --output')
        commit = git('rev-parse', 'HEAD', root=args.source_root)
        inventory = inventory_at(commit, args.source_root)
        args.output.write_text(json.dumps(inventory, indent=2) + '\n')
        folder = args.output.parent
        (folder / 'SHA256SUMS').write_text(''.join(
            hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name + '\n'
            for p in sorted(folder.iterdir()) if p.is_file() and p.name != 'SHA256SUMS'))
    elif args.command == 'notify':
        if not args.tag:
            parser.error('notify requires --tag')
        notify(args.tag)
    else:
        protect()


if __name__ == '__main__':
    main()
