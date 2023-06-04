import json
import re
import subprocess
from urllib.parse import urljoin

import pygit2

REPOS = [("https://github.com/nil-vr/nil.qr/", "nil.qr")]
VERSION_TAG = re.compile(r"refs/tags/(\d+\.\d+\.\d+)")

packages = {}
for repo_info in REPOS:
    remote = repo_info[0]
    name = repo_info[1]

    repo = pygit2.init_repository(name, bare=True, origin_url=remote)
    subprocess.run(
        ("git", "fetch", "--filter=blob:none", "origin", "refs/tags/*:refs/tags/*"),
        cwd=name,
        check=True,
    )

    versions = []
    for ref in repo.listall_reference_objects():
        version_match = VERSION_TAG.fullmatch(ref.name)
        if version_match is None:
            continue
        commit = ref.peel(pygit2.GIT_OBJ_COMMIT)
        blob = commit.tree / "Packages" / name / "package.json"
        versions.append((version_match[1], blob))

    args = ["git", "fetch", "origin"]
    args.extend((str(v[1].id) for v in versions))
    subprocess.run(args, cwd=name, check=True)

    package_versions = {}
    for version_info in versions:
        version = version_info[0]
        blob = version_info[1]
        version_data = json.loads(blob.data)
        version_data["url"] = urljoin(
            remote, f"releases/download/{version}/{name}-{version}.zip"
        )
        package_versions[version] = version_data

    packages[name] = {
        "versions": package_versions,
    }

with open("out/index.json", "w") as vpm:
    json.dump(
        {
            "packages": packages,
            "author": "nil",
            "id": "nil.github",
            "name": "nil's packages",
            "url": "https://nil-vr.github.io/vpm/index.json",
        },
        vpm,
    )
