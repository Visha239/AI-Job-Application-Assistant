from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceSelection:
    jobspy_sites: tuple[str, ...]
    include_naukri: bool
    include_company_careers: bool
    selected_companies: tuple[str, ...]

    @property
    def has_any_source(self) -> bool:
        return bool(
            self.jobspy_sites
            or self.include_naukri
            or self.include_company_careers
        )

    def validate(self) -> None:
        if not self.has_any_source:
            raise ValueError(
                "Select at least one job source."
            )

        if (
            self.include_company_careers
            and not self.selected_companies
        ):
            raise ValueError(
                "Choose at least one target company, or disable "
                "official company-careers search."
            )


def build_source_selection(
    *,
    jobspy_sites: list[str] | None,
    include_naukri: bool,
    include_company_careers: bool,
    selected_companies: list[str] | None,
) -> SourceSelection:
    selection = SourceSelection(
        jobspy_sites=tuple(jobspy_sites or []),
        include_naukri=bool(include_naukri),
        include_company_careers=bool(
            include_company_careers
        ),
        selected_companies=tuple(selected_companies or []),
    )
    selection.validate()
    return selection
