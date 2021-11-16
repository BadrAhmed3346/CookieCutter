import datetime as dt
import os
import re
from pathlib import Path
from typing import Iterable

import git
import github.PullRequest
import github.Repository
from github import Github
from jinja2 import Template

CURRENT_FILE = Path(__file__)
ROOT = CURRENT_FILE.parents[1]
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", None)
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY", None)
DEFAULT_BRANCH = "master"

# Generate changelog for PRs merged yesterday
MERGED_DATE = dt.date.today() - dt.timedelta(days=1)
RELEASE = f"{MERGED_DATE:%Y.%m.%d}"


def main() -> None:
    """
    Script entry point.
    """
    repo = Github(login_or_token=GITHUB_TOKEN).get_repo(GITHUB_REPO)
    merged_pulls = list(iter_pulls(repo))
    if not merged_pulls:
        print("Nothing was merged, existing.")
        return

    # Group pull requests by type of change
    grouped_pulls = group_pulls_by_change_type(merged_pulls)

    # Generate portion of markdown
    release_changes_summary = generate_md(grouped_pulls)

    # Update CHANGELOG.md file
    changelog_path = ROOT / "CHANGELOG.md"
    write_changelog(changelog_path, release_changes_summary)

    # Update version
    setup_py_path = ROOT / "setup.py"
    update_version(setup_py_path, RELEASE)

    # Commit changes, create tag and push
    update_git_repo([changelog_path, setup_py_path], RELEASE)

    # Create GitHub release
    repo.create_git_release(
        tag=RELEASE,
        name=RELEASE,
        message=release_changes_summary,
    )


def iter_pulls(
    repo: github.Repository.Repository,
) -> Iterable[github.PullRequest.PullRequest]:
    """Fetch merged pull requests at the date we're interested in."""
    recent_pulls = repo.get_pulls(
        state="closed", sort="updated", direction="desc"
    ).get_page(0)
    for pull in recent_pulls:
        if pull.merged and pull.merged_at.date() == MERGED_DATE:
            yield pull


def group_pulls_by_change_type(
    pull_requests_list: list[github.PullRequest.PullRequest],
) -> dict[str, list[github.PullRequest.PullRequest]]:
    """Group pull request by change type."""
    grouped_pulls = {
        "Changed": [],
        "Fixed": [],
        "Updated": [],
    }
    for pull in pull_requests_list:
        label_names = {l.name for l in pull.labels}
        if "update" in label_names:
            group_name = "Updated"
        elif "bug" in label_names:
            group_name = "Fixed"
        else:
            group_name = "Changed"
        grouped_pulls[group_name].append(pull)
    return grouped_pulls


def generate_md(grouped_pulls: dict[str, list[github.PullRequest.PullRequest]]) -> str:
    """Generate markdown file from Jinja template."""
    changelog_template = ROOT / ".github" / "changelog-template.md"
    template = Template(changelog_template.read_text(), autoescape=True)
    return template.render(merge_date=MERGED_DATE, grouped_pulls=grouped_pulls)


def write_changelog(file_path: Path, content: str) -> None:
    """Write Release details to the changelog file."""
    old_content = file_path.read_text()
    updated_content = old_content.replace(
        "<!-- GENERATOR_PLACEHOLDER -->",
        f"<!-- GENERATOR_PLACEHOLDER -->\n\n{content}",
    )
    file_path.write_text(updated_content)


def update_version(file_path: Path, release: str) -> None:
    """Update template version in setup.py."""
    old_content = file_path.read_text()
    updated_content = re.sub(
        r'\nversion = "\d+\.\d+\.\d+"\n',
        f'version = "{release}"',
        old_content,
    )
    file_path.write_text(updated_content)


def update_git_repo(paths: list[Path], release: str) -> None:
    """Commit, tag changes in git repo and push to origin."""
    repo = git.Repo(".")
    for path in paths:
        repo.git.add(path)
    repo.git.commit(
        m=f"Release {release}",
        author="GitHub Actions <actions@github.com>",
    )
    repo.git.tag("-a", release)
    server = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git"
    repo.git.push(server, DEFAULT_BRANCH)
    repo.git.push("--tags", server, DEFAULT_BRANCH)


if __name__ == "__main__":
    if GITHUB_REPO is None:
        raise RuntimeError(
            "No github repo, please set the environment variable GITHUB_REPOSITORY"
        )
    main()
