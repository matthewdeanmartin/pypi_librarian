# coding=utf-8
"""
Extended CLI tests for pypi-librarian.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pypi_librarian.__main__ import main
from pypi_librarian.models import Project, Package, NewPackage, ProjectInfo
from pypi_librarian.pypistats import DownloadStats
from pypi_librarian.github import GitHubInfo
from pypi_librarian.health import HealthScore


class TestCLIExtended:
    @patch("pypi_librarian.__main__.Repository")
    def test_info_command(self, MockRepo, capsys):
        mock_repo = MockRepo.return_value
        project = Project(
            name="test-pkg",
            info=ProjectInfo(
                name="test-pkg",
                version="1.0.0",
                summary="A test package",
                author="Test Author",
                author_email="test@example.com",
                maintainer=None,
                maintainer_email=None,
                license="MIT",
                requires_python=">=3.8",
                project_url="https://example.com",
                home_page="https://example.com",
                classifiers=("License :: OSI Approved :: MIT License",),
                keywords="test",
                description="desc",
                description_content_type="text/plain",
                requires_dist=("requests>=2.0",),
                yanked=False,
                yanked_reason=None,
                raw={}
            ),
            releases=[],
            latest_files=[],
            raw={}
        )
        mock_repo.get_project.return_value = project

        exit_code = main(["info", "test-pkg"])
        
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Name:           test-pkg" in captured.out
        assert "Version:        1.0.0" in captured.out
        assert "Summary:        A test package" in captured.out
        assert "License:        MIT" in captured.out
        assert "Classifiers:" in captured.out
        assert "  License :: OSI Approved :: MIT License" in captured.out

    @patch("pypi_librarian.__main__.Repository")
    def test_versions_command(self, MockRepo, capsys):
        mock_repo = MockRepo.return_value
        project = Project(
            name="test-pkg",
            info=MagicMock(name="test-pkg"),
            releases=[
                MagicMock(version="1.0.0", files=[1, 2]),
                MagicMock(version="0.9.0", files=[1]),
            ],
            latest_files=[],
            raw={}
        )
        mock_repo.get_project.return_value = project

        exit_code = main(["versions", "test-pkg"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "1.0.0  (2 files)" in captured.out
        assert "0.9.0  (1 file)" in captured.out

    @patch("pypi_librarian.__main__.Repository")
    def test_latest_command(self, MockRepo, capsys):
        mock_repo = MockRepo.return_value
        mock_repo.newest_packages.return_value = [
            NewPackage(title="pkg1 1.0.0", link="https://pypi.org/p/pkg1", description="desc1", published=""),
            NewPackage(title="pkg2 2.0.0", link="https://pypi.org/p/pkg2", description="desc2", published=""),
        ]

        exit_code = main(["latest"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "pkg1 1.0.0" in captured.out
        assert "pkg2 2.0.0" in captured.out
        assert "desc1" in captured.out

    @patch("pypi_librarian.__main__.Repository")
    @patch("pypi_librarian.pypistats.fetch_download_stats")
    @patch("pypi_librarian.github.fetch_github_info_for_project")
    @patch("pypi_librarian.health.score_project")
    def test_enrich_command(self, MockScore, MockGithub, MockStats, MockRepo, capsys):
        mock_repo = MockRepo.return_value
        info = ProjectInfo(
            name="test-pkg", version="1.0.0", summary="summary", author="author",
            author_email="email", maintainer=None, maintainer_email=None,
            license="MIT", home_page="url", project_url="url", requires_python=">=3.8",
            classifiers=(), keywords=None, description=None, description_content_type=None,
            requires_dist=(), yanked=False, yanked_reason=None, raw={}
        )
        project = Project(
            name="test-pkg",
            info=info,
            releases=[],
            latest_files=[],
            raw={}
        )

        mock_repo.get_project.return_value = project
        
        MockStats.return_value = DownloadStats(package="test-pkg", last_day=10, last_week=70, last_month=300, raw={})
        MockGithub.return_value = GitHubInfo(
            owner="owner", repo="repo", stars=100, forks=20, open_issues=5,
            last_push="2024-01-01", description="desc", archived=False, raw={}
        )
        MockScore.return_value = HealthScore(score=0.85, components={}, notes=["Note 1"])

        exit_code = main(["enrich", "test-pkg"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Package: test-pkg  1.0.0" in captured.out
        assert "Download stats (pypistats.org):" in captured.out
        assert "  Last month: 300" in captured.out
        assert "GitHub (owner/repo):" in captured.out
        assert "  Stars:       100" in captured.out
        assert "Health score: 0.85 / 1.00" in captured.out
        assert "    - Note 1" in captured.out

    @patch("pypi_librarian.__main__.Repository")
    def test_info_command_not_found(self, MockRepo, capsys):
        mock_repo = MockRepo.return_value
        mock_repo.get_project.side_effect = ValueError("Not found")

        exit_code = main(["info", "missing-pkg"])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Error: Not found" in captured.err
