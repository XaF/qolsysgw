#!/usr/bin/env python3

import argparse
import json
import os
import re
import requests
import shlex


class ChangeLogRegex(object):
    NEXT = re.compile(
        r'(?P<prefix>(?P<header>{%\s*if true\s*-?%}\s*'
        r'### _Next \(dev\)_\n*)'
        r'(?P<release_desc>[^\n].*?[^\n]))'
        r'(?P<suffix>\n*{%\s*endif\s*-?%})',
        re.DOTALL,
    )
    NEXT_SUB = re.compile(
        r'(?P<before>{%\s*if )true(?P<between>\s*-?%}\s*### )'
        r'_Next \(dev\)_(?P<after>\n)',
        re.IGNORECASE,
    )
    VERSION = re.compile(
        r'{%\s*if parsed_version < \['
        r'(?P<major>[0-9]*), (?P<minor>[0-9]*), (?P<patch>[0-9]*)\]'
        r'\s*-%}\s*### (?P<release_name>[^\n]*)\n*'
        r'(?P<release_desc>[^\n].*?[^\n])'
        r'\n*{%\s*endif\s*-?%}',
        re.DOTALL,
    )
    CHANGE = re.compile(
        r'^\s*\*\s*(?P<change>.*)$',
        re.MULTILINE,
    )

    COMMIT_CHANGE = re.compile(
        r'^\s*(\*\*)?\[(?P<category>[^\]]*)\](\*\*)?\s*'
        r'(?P<change>.*)$',
    )
    COMMIT_CHANGE_BUG = re.compile(r'\b(bug|fix)\b', re.IGNORECASE)
    COMMIT_CHANGE_FEATURE = re.compile(r'\b(feature|add)\b', re.IGNORECASE)


class ChangeLogHandler(object):

    CHANGELOG_FILE = 'info.md'
    RELEASE_PATHS = [
        re.compile(r'^apps/'),
    ]

    def __init__(self, github_event, github_token=None):
        self._changelog = None
        self._gh_event = github_event

        if github_token:
            self._headers = {'Authorization': f'Bearer {github_token}'}
        else:
            self._headers = {}

    @property
    def repo(self):
        return self._gh_event['repository']['full_name']

    @property
    def commits(self):
        return self._gh_event['commits']

    @property
    def before_sha(self):
        return self._gh_event['before']

    def printenv(self):
        new_release = self.new_release()

        publish_release = str(bool(new_release)).lower()
        print(f'PUBLISH_RELEASE={publish_release}')

        if new_release:
            print(f'RELEASE_VERSION={new_release["version"]}')
            print(f'RELEASE_MAJOR={new_release["major"]}')
            print(f'RELEASE_MINOR={new_release["minor"]}')
            print(f'RELEASE_PATCH={new_release["patch"]}')
            print(f'RELEASE_VERSION_MAJOR={new_release["major"]}')
            print(f'RELEASE_VERSION_MINOR={new_release["major"]}.'
                  f'{new_release["minor"]}')
            print(f'RELEASE_VERSION_PATCH={new_release["major"]}.'
                  f'{new_release["minor"]}.{new_release["patch"]}')
            print(f'RELEASE_NAME={shlex.quote(new_release["release_name"])}')

            print('RELEASE_DESC<<EOM')
            print(f'{new_release["release_desc"]}')
            print('EOM')

    def read_file(self):
        if self._changelog is None:
            with open(self.CHANGELOG_FILE, 'r') as f:
                self._changelog = f.read()

        return self._changelog

    def categorize_change(self, change):
        formatted = ChangeLogRegex.COMMIT_CHANGE.search(change)
        if formatted:
            return (formatted['category'], formatted['change'])

        bug = ChangeLogRegex.COMMIT_CHANGE_BUG.search(change)
        if bug:
            return ('bugfix', change)

        feature = ChangeLogRegex.COMMIT_CHANGE_FEATURE.search(change)
        if feature:
            return ('feature', change)

        return (None, change)

    def get_new_changes(self):
        if not hasattr(self, '_new_changes'):
            new_changes = []

            for commit in self.commits:
                resp = requests.get(
                    f'https://api.github.com/repos/{self.repo}'
                    f'/commits/{commit["id"]}',
                    headers=self._headers,
                )
                if not resp.ok:
                    raise RuntimeError(f'Unable to get details on commit {commit["id"]}')

                details = resp.json()
                file_match = False
                for file in details['files']:
                    for release_path in self.RELEASE_PATHS:
                        if release_path.search(file['filename']):
                            file_match = True
                            break
                    if file_match:
                        break

                if file_match:
                    short_message = commit['message'].splitlines()[0]
                    new_changes.append(short_message)

            self._new_changes = [self.categorize_change(c) for c in new_changes]

        return self._new_changes

    def get_changes(self, existing_changes=None):
        new_changes = self.get_new_changes()

        if new_changes and existing_changes:
            new_changes = [c for c in new_changes if c not in existing_changes]

        if not new_changes:
            return None

        return new_changes

    def read_file_releases(self):
        for version in ChangeLogRegex.VERSION.finditer(self.read_file()):
            d = version.groupdict()

            for k in ['major', 'minor', 'patch']:
                d[k] = int(d.get(k, 0))

            d['version_tuple'] = (d['major'], d['minor'], d['patch'])
            d['version'] = '.'.join([str(v) for v in d['version_tuple']])

            yield d

    def new_release(self):
        # If we have a next block in the changelog file, we know we're not
        # going to create a new release at this time
        if ChangeLogRegex.NEXT.search(self.read_file()):
            return False

        # If there is no NEXT block, we need to check the last version and
        # compare it with the last version in the changelog
        releases = list(self.read_file_releases())
        if not releases:
            # If we don't have any version in the file, no need to proceed
            return False

        resp = requests.get(
            f'https://api.github.com/repos/{self.repo}'
            '/releases/latest',
            headers=self._headers,
        )
        if not resp.ok:
            if resp.status_code == 404:
                return releases[0]
            else:
                return False

        release = resp.json()
        tag = release['tag_name']
        version = tuple(int(v) for v in tag.replace('v', '').split('.'))

        if version < releases[0]['version_tuple']:
            return releases[0]

        return False

    def update_changelog(self):
        existing_changes = []

        next_version = ChangeLogRegex.NEXT.search(self.read_file())
        if next_version:
            for change in ChangeLogRegex.CHANGE.finditer(next_version['release_desc']):
                change_text = change['change']
                existing_changes.append(self.categorize_change(change_text))

        changes = self.get_changes(existing_changes=existing_changes)
        if not changes:
            return

        new_changes = []
        for (changecat, change) in changes:
            cat = f'**[{changecat}]** ' if changecat else ''
            new_changes.append(f' * {cat}{change}')
        new_changes = '\n'.join(new_changes)

        if next_version:
            new_content = ChangeLogRegex.NEXT.sub(
                f'\g<prefix>\n{new_changes}\g<suffix>',
                self.read_file(),
            )
        else:
            new_content = re.sub(
                '(## ChangeLog)',
                '\g<1>\n{%   if true -%}\n### _Next (dev)_\n\n'
                f'{new_changes}\n'
                '{%   endif %}',
                self.read_file(),
                re.IGNORECASE,
            )

        with open(self.CHANGELOG_FILE, 'w') as f:
            f.write(new_content)

    def release_next(self, version):
        if not ChangeLogRegex.NEXT_SUB.search(self.read_file()):
            raise RuntimeError('No release waiting to be released')

        version_parts = ['major', 'minor', 'patch']
        if version in version_parts:
            releases = list(self.read_file_releases())
            last_release = releases[0]

            idx = version_parts.index(version)
            new_version = {
                k: last_release[k] if i <= idx else 0
                for i, k in enumerate(version_parts)
            }
            new_version[version] += 1

            version = new_version
        else:
            version = version.replace('v', '').split('.')
            version = {
                'major': int(version[0]),
                'minor': int(version[1]),
                'patch': int(version[2]),
            }

        major = version['major']
        minor = version['minor']
        patch = version['patch']

        new_content = ChangeLogRegex.NEXT_SUB.sub(
            f'\g<before>parsed_version < [{major}, {minor}, {patch}]'
            f'\g<between>Version {major}.{minor}.{patch}\g<after>',
            self.read_file(),
            re.IGNORECASE,
        )

        with open(self.CHANGELOG_FILE, 'w') as f:
            f.write(new_content)

        print(f'Replaced NEXT by release {major}.{minor}.{patch}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-e', '--github-event', type=json.loads,
        default=json.loads(os.getenv('GITHUB_EVENT')) if os.getenv('GITHUB_EVENT') else None,
        help='The JSON github event, returned by ${{ toJSON(github.event) }}',
    )

    parser.add_argument(
        '-t', '--github-token', type=str,
        default=os.getenv('GITHUB_TOKEN'),
        help='If the repository is private, the github token to access it',
    )

    command = parser.add_mutually_exclusive_group(required=True)
    command.add_argument(
        '-p', '--printenv', '--print-env',
        action='store_true',
        help='Print the environment variables useful for the process and exit',
    )
    command.add_argument(
        '-u', '--update-changelog',
        action='store_true',
        help='Update the changelog file',
    )
    command.add_argument(
        '-r', '--release-next',
        nargs='?', const='patch',
        help='Release the next version',
    )

    args = parser.parse_args()

    handler = ChangeLogHandler(
        github_event=args.github_event,
        github_token=args.github_token,
    )

    if args.printenv:
        handler.printenv()
    elif args.update_changelog:
        handler.update_changelog()
    elif args.release_next:
        handler.release_next(args.release_next)

