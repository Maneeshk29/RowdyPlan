"""Handshake job ingestion through an Apify Actor or Task."""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import settings
from app.ingestion.base_provider import UniversityOpportunityProvider
from app.ingestion.normalization import deduplicate, normalize_opportunity


COMMON_SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "sql", "postgresql", "mysql", "mongodb", "redis", "react", "angular",
    "vue", "node.js", "express", "django", "flask", "fastapi",
    "spring", "spring boot", "html", "css", "tailwind", "aws", "azure",
    "gcp", "docker", "kubernetes", "terraform", "linux", "git",
    "github", "jira", "agile", "scrum", "rest api", "graphql",
    "machine learning", "deep learning", "data analysis", "data science",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "spark",
    "tableau", "power bi", "excel", "cybersecurity", "network security",
    "siem", "incident response", "vulnerability assessment", "communication",
    "leadership", "teamwork", "problem solving", "technical writing",
    "product management", "user research", "mobile development",
    "react native", "flutter", "swift", "kotlin",
]


class HandshakeProvider(UniversityOpportunityProvider):
    """
    Fetch Handshake postings from Apify and normalize them for Rowdy Plan.

    Configure either APIFY_HANDSHAKE_TASK_ID or APIFY_HANDSHAKE_ACTOR_ID.
    A task is recommended when the Handshake actor has a complex input schema.
    """

    def __init__(
        self,
        actor_id: str | None = None,
        task_id: str | None = None,
        actor_input: dict[str, Any] | None = None,
        token: str | None = None,
        timeout_seconds: int | None = None,
        dataset_id: str | None = None,
        use_latest_run: bool = False,
    ):
        self.source = "handshake"
        self.actor_id = actor_id or settings.APIFY_HANDSHAKE_ACTOR_ID
        self.task_id = task_id or settings.APIFY_HANDSHAKE_TASK_ID
        self.token = token or settings.APIFY_API_TOKEN
        self.timeout_seconds = timeout_seconds or settings.APIFY_TIMEOUT_SECONDS
        self.dataset_id = dataset_id
        self.use_latest_run = use_latest_run
        self.actor_input = {
            **(settings.APIFY_HANDSHAKE_INPUT or {}),
            **(actor_input or {}),
        }

    async def fetch_jobs(self) -> list[dict]:
        raw_items = await self._run_apify()
        jobs = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            job = self._normalize_handshake_job(item)
            if job:
                jobs.append(job)
        return deduplicate(jobs)

    async def fetch_events(self) -> list[dict]:
        return []

    async def fetch_research(self) -> list[dict]:
        return []

    async def fetch_organizations(self) -> list[dict]:
        return []

    async def fetch_programs(self) -> list[dict]:
        return []

    async def _run_apify(self) -> list[dict]:
        if not self.token:
            raise ValueError("APIFY_API_TOKEN is required for Handshake ingestion.")
        if not self.dataset_id and not self.actor_id and not self.task_id:
            raise ValueError(
                "Set APIFY_HANDSHAKE_ACTOR_ID or APIFY_HANDSHAKE_TASK_ID for Handshake ingestion."
            )

        collection = "actor-tasks" if self.task_id else "actors"
        identifier = self.task_id or self.actor_id or ""
        encoded_id = quote(identifier.replace("/", "~"), safe="~")
        params = {"clean": "true", "format": "json"}
        if self.dataset_id:
            encoded_dataset = quote(self.dataset_id, safe="~")
            url = f"https://api.apify.com/v2/datasets/{encoded_dataset}/items"
        elif self.use_latest_run:
            url = f"https://api.apify.com/v2/{collection}/{encoded_id}/runs/last/dataset/items"
            params["status"] = "SUCCEEDED"
        else:
            url = f"https://api.apify.com/v2/{collection}/{encoded_id}/run-sync-get-dataset-items"

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            headers = {"Authorization": f"Bearer {self.token}"}
            if self.dataset_id or self.use_latest_run:
                response = await client.get(url, headers=headers, params=params)
                if response.status_code == 404 and self.use_latest_run and not self.dataset_id:
                    raise ValueError("No successful Handshake run was found. Run the scraper in Apify first.")
            else:
                response = await client.post(url, headers=headers, params=params, json=self.actor_input)
            response.raise_for_status()

        payload = response.json()
        if isinstance(payload, list):
            return payload

        if isinstance(payload, dict):
            if isinstance(payload.get("items"), list):
                return payload["items"]
            if isinstance(payload.get("data"), dict) and isinstance(payload["data"].get("items"), list):
                return payload["data"]["items"]
            status = str(payload.get("status", "")).upper()
            if status in {"READY", "RUNNING"}:
                raise RuntimeError(
                    "Apify run did not finish in the sync window. Use a smaller input, "
                    "an Apify task with fewer results, or switch this endpoint to a background job."
                )

        raise RuntimeError("Apify returned an unexpected Handshake payload.")

    def _normalize_handshake_job(self, raw: dict[str, Any]) -> dict | None:
        title = _pick(
            raw,
            "title", "jobTitle", "job_title", "name", "positionTitle",
            "position", "role",
        )
        if not title:
            return None

        organization_value = _pick(
            raw,
            "company.name", "employer.name", "organization.name",
            "organization", "company", "companyName", "company_name",
            "employer", "employerName", "employer_name", "company.name",
            "employer.name",
        )
        organization = _clean_text(" ".join(_coerce_list(organization_value)))

        description_parts = _coerce_list(_pick(raw, "descriptionText", "description_text"), split_strings=False) or _pick_many(
            raw,
            "description", "jobDescription", "job_description", "details",
            "summary", "responsibilities", "about", "body", "descriptionHtml", "description_html",
        )
        requirement_parts = _pick_many(
            raw,
            "requirements", "qualifications", "minimumQualifications",
            "minimum_qualifications", "preferredQualifications",
            "preferred_qualifications", "eligibility",
        )
        description = _clean_text(" ".join(description_parts))
        requirements_text = _clean_text(" ".join(requirement_parts))
        searchable_text = _clean_text(
            " ".join([title, organization, description, requirements_text])
        )

        explicit_skills = _coerce_list(
            _pick(raw, "skills", "skillTags", "skill_tags", "tags", "labels")
        )
        skills = _dedupe_strings(explicit_skills + _extract_skills(searchable_text))
        requirements = _dedupe_strings(
            _coerce_list(_pick(raw, "requirements", "qualifications", "eligibility"))
            + _split_requirements(requirements_text)
        )
        majors = _dedupe_strings(_coerce_list(_pick(
            raw,
            "majors", "eligibleMajors", "eligible_majors", "preferredMajors",
            "preferred_majors", "majorGroups", "major_groups",
        )))
        graduation_years = _dedupe_strings(_coerce_list(_pick(
            raw,
            "graduationYears", "graduation_years", "gradYears", "grad_years",
            "schoolYears", "school_years", "classifications",
        )))
        if not graduation_years:
            graduation_years = _extract_graduation_years(searchable_text)

        location_parts = _coerce_list(_pick(
            raw,
            "location", "locations", "jobLocation", "job_location",
        ), split_strings=False)
        workplace = _pick(raw, "workplace", "workplaceType", "workplace_type")
        location = _clean_text(" / ".join(_dedupe_strings(location_parts + _coerce_list(workplace))))
        deadline = _parse_datetime(_pick(
            raw,
            "deadline", "expirationDate", "expiration_date", "expiresAt",
            "expires_at", "applicationDeadline", "application_deadline",
            "applyBy", "apply_by",
        ))
        url = _pick(
            raw,
            "url", "jobUrl", "job_url", "applyUrl", "apply_url",
            "applicationUrl", "application_url", "externalUrl", "external_url",
        )
        source_id = str(_pick(raw, "id", "jobId", "job_id", "postingId", "posting_id", "handshakeId") or "")
        employment_type = _pick(
            raw,
            "employmentTypes", "employment_types",
            "employmentType", "employment_type", "jobType", "job_type",
            "type", "category",
        )
        employment_type_text = ", ".join(_coerce_list(employment_type))

        normalized = normalize_opportunity(
            {
                "title": title,
                "description": description or requirements_text,
                "organization": organization,
                "skills": skills,
                "requirements": requirements,
                "majors": majors,
                "graduation_years": graduation_years,
                "location": location,
                "deadline": deadline,
                "url": url,
                "source_timestamp": _parse_datetime(raw.get("collectedAt")) or datetime.utcnow().isoformat(),
                "minimum_gpa": _extract_minimum_gpa(raw, searchable_text),
                "work_authorization_required": _requires_work_authorization(raw, searchable_text),
            },
            self.source,
            "job",
        )
        normalized.update({
            "source_id": source_id,
            "required_skills": skills,
            "required_majors": majors,
            "job_type": employment_type_text,
            "employment_type": employment_type_text,
            "compensation": _format_compensation(_pick(raw, "compensation", "salary", "pay", "wage")),
            "role_types": _coerce_list(_pick(raw, "roleTypes", "role_types")),
            "industry": _pick(raw, "employer.industry", "company.industry", "industry") or "",
            "workplace": workplace or "",
            "posted_at": _parse_datetime(raw.get("postedAt")),
            "source_payload": "apify",
        })
        return normalized


def _format_compensation(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, dict):
        return _clean_text(str(value))

    minimum = value.get("minAmount")
    maximum = value.get("maxAmount")
    if minimum is None and maximum is None:
        return ""
    amount = str(minimum if minimum is not None else maximum)
    if minimum is not None and maximum is not None and minimum != maximum:
        amount = f"{minimum}-{maximum}"
    currency = str(value.get("currency") or "").strip()
    cadence = str(value.get("cadence") or "").strip()
    return f"{currency} {amount}".strip() + (f"/{cadence}" if cadence else "")


def _pick(raw: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = _get_nested(raw, key)
        if value not in (None, "", [], {}):
            return value
    return None


def _pick_many(raw: dict[str, Any], *keys: str) -> list[str]:
    values: list[str] = []
    for key in keys:
        value = _get_nested(raw, key)
        values.extend(_coerce_list(value))
    return values


def _get_nested(raw: dict[str, Any], key: str) -> Any:
    current: Any = raw
    for part in key.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _coerce_list(value: Any, *, split_strings: bool = True) -> list[str]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, str):
        if value.strip().startswith("["):
            try:
                decoded = json.loads(value)
                return _coerce_list(decoded, split_strings=split_strings)
            except json.JSONDecodeError:
                pass
        if not split_strings:
            return [value.strip()] if value.strip() else []
        return [part.strip() for part in re.split(r"[,;\n|]+", value) if part.strip()]
    if isinstance(value, dict):
        for key in ("name", "title", "label", "value", "text"):
            if value.get(key):
                return [str(value[key]).strip()]
        return [
            str(v).strip()
            for v in value.values()
            if isinstance(v, (str, int, float)) and str(v).strip()
        ]
    if isinstance(value, list):
        items: list[str] = []
        for item in value:
            items.extend(_coerce_list(item, split_strings=split_strings))
        return items
    return [str(value).strip()]


def _clean_text(value: str) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", str(value))
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", text).strip()


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = _clean_text(str(value))
        if not cleaned:
            continue
        key = cleaned.lower()
        if key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def _extract_skills(text: str) -> list[str]:
    haystack = f" {_clean_text(text).lower()} "
    found = []
    for skill in COMMON_SKILLS:
        pattern = r"(?<![a-z0-9+#.])" + re.escape(skill.lower()) + r"(?![a-z0-9+#.])"
        if re.search(pattern, haystack):
            found.append(skill)
    return found


def _split_requirements(text: str) -> list[str]:
    cleaned = _clean_text(text)
    if not cleaned:
        return []
    pieces = re.split(r"(?:\s+[•*-]\s+)|(?:\s+\d+\.\s+)|(?:;\s+)", cleaned)
    return [piece.strip() for piece in pieces if 4 <= len(piece.strip()) <= 180]


def _parse_datetime(value: Any) -> str | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    text = str(value).strip()
    if not text:
        return None
    if text.isdigit():
        timestamp = int(text)
        if timestamp > 10_000_000_000:
            timestamp = timestamp // 1000
        return datetime.utcfromtimestamp(timestamp).isoformat()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(text.replace("Z", ""), fmt).isoformat()
        except ValueError:
            continue
    return text


def _extract_minimum_gpa(raw: dict[str, Any], text: str) -> float | None:
    direct = _pick(raw, "minimum_gpa", "minimumGpa", "minGpa", "gpa")
    if direct not in (None, ""):
        try:
            gpa = float(str(direct).replace("+", ""))
            return gpa if 0 <= gpa <= 4 else None
        except ValueError:
            pass

    match = re.search(r"(?:gpa|grade point average)[^\d]{0,12}([0-4](?:\.\d{1,2})?)\+?", text.lower())
    if match:
        return float(match.group(1))
    return None


def _extract_graduation_years(text: str) -> list[str]:
    years = re.findall(r"\b20[2-4]\d\b", text)
    return _dedupe_strings(years)


def _requires_work_authorization(raw: dict[str, Any], text: str) -> bool:
    direct = _pick(
        raw,
        "work_authorization_required", "workAuthorizationRequired",
        "requiresWorkAuthorization", "requires_work_authorization",
        "sponsorship", "visaSponsorship", "visa_sponsorship",
    )
    if isinstance(direct, bool):
        return direct
    if isinstance(direct, str):
        low = direct.lower()
        if low in {"true", "yes", "required", "authorized", "no sponsorship"}:
            return True
        if low in {"false", "no", "not required"}:
            return False

    low_text = text.lower()
    auth_phrases = (
        "us citizenship required",
        "u.s. citizenship required",
        "must be authorized to work",
        "authorized to work in the united states",
        "sponsorship is not available",
        "will not sponsor",
    )
    return any(phrase in low_text for phrase in auth_phrases)
