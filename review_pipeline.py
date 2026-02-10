import importlib
from dataclasses import dataclass
from io import BytesIO
from typing import Dict, List, Optional


@dataclass
class DocumentMetadata:
    name: str
    file_type: str
    word_count: int
    character_count: int


@dataclass
class ReviewFinding:
    title: str
    severity: str
    observation: str
    recommendation: str
    azure_alignment: str


CHECKS: List[Dict[str, object]] = [
    {
        "id": "identity_access",
        "title": "Identity and access management",
        "severity": "critical",
        "keywords": ["identity", "iam", "entra", "azure ad", "rbac", "role"],
        "recommendation": (
            "Define identity boundaries and apply Azure RBAC with least privilege. "
            "Prefer Microsoft Entra ID for centralized access control and conditional access."
        ),
        "azure_alignment": "Microsoft Entra ID, Azure RBAC, Conditional Access",
    },
    {
        "id": "network_security",
        "title": "Network segmentation and security",
        "severity": "critical",
        "keywords": ["vnet", "subnet", "network", "firewall", "nsg", "private"],
        "recommendation": (
            "Describe network segmentation, private endpoints, and egress control. "
            "Use NSGs and Azure Firewall to enforce traffic rules."
        ),
        "azure_alignment": "Virtual Network, NSG, Azure Firewall, Private Link",
    },
    {
        "id": "resiliency",
        "title": "Resiliency and availability",
        "severity": "critical",
        "keywords": ["availability", "zone", "failover", "disaster", "recovery"],
        "recommendation": (
            "Define availability targets, zone-redundancy, and DR strategy. "
            "Use Azure Availability Zones and paired regions for resilience."
        ),
        "azure_alignment": "Availability Zones, Azure Site Recovery, Paired Regions",
    },
    {
        "id": "monitoring",
        "title": "Monitoring and observability",
        "severity": "high",
        "keywords": ["monitoring", "logging", "telemetry", "metrics", "alert"],
        "recommendation": (
            "Add monitoring coverage, dashboards, and alerting. "
            "Centralize logs with Azure Monitor and Log Analytics."
        ),
        "azure_alignment": "Azure Monitor, Log Analytics, Application Insights",
    },
    {
        "id": "data_protection",
        "title": "Data protection and backup",
        "severity": "high",
        "keywords": ["backup", "retention", "encryption", "key", "kms"],
        "recommendation": (
            "Document data classification, encryption, and backup policies. "
            "Use Azure Key Vault for keys and Azure Backup for recovery."
        ),
        "azure_alignment": "Azure Key Vault, Azure Backup, Azure Storage encryption",
    },
    {
        "id": "cost_governance",
        "title": "Cost management and governance",
        "severity": "medium",
        "keywords": ["cost", "budget", "tag", "governance", "policy"],
        "recommendation": (
            "Define tagging standards, budgets, and policy controls. "
            "Use Azure Policy and Cost Management to enforce governance."
        ),
        "azure_alignment": "Azure Policy, Cost Management, Management Groups",
    },
    {
        "id": "security_operations",
        "title": "Security operations",
        "severity": "medium",
        "keywords": ["security", "defender", "siem", "soc", "threat"],
        "recommendation": (
            "Describe security monitoring, threat detection, and incident response. "
            "Leverage Microsoft Defender for Cloud and Microsoft Sentinel."
        ),
        "azure_alignment": "Defender for Cloud, Microsoft Sentinel",
    },
    {
        "id": "performance",
        "title": "Performance and scalability",
        "severity": "medium",
        "keywords": ["scale", "performance", "throughput", "latency", "autoscale"],
        "recommendation": (
            "Include performance targets and scaling strategy. "
            "Use autoscale and caching patterns where applicable."
        ),
        "azure_alignment": "Azure Autoscale, Azure Cache for Redis",
    },
    {
        "id": "ci_cd",
        "title": "CI/CD and delivery",
        "severity": "low",
        "keywords": ["pipeline", "ci", "cd", "deployment", "devops"],
        "recommendation": (
            "Define delivery pipelines, infrastructure as code, and release gates. "
            "Use Azure DevOps or GitHub Actions with ARM/Bicep/Terraform."
        ),
        "azure_alignment": "Azure DevOps, GitHub Actions, Bicep, Terraform",
    },
]


def _optional_import(module_name: str):
    if importlib.util.find_spec(module_name) is None:
        return None
    return importlib.import_module(module_name)


def extract_text(file_name: str, file_bytes: bytes) -> str:
    file_type = file_name.split(".")[-1].lower()
    if file_type in {"txt", "md"}:
        return file_bytes.decode("utf-8", errors="ignore")

    if file_type == "pdf":
        pypdf = _optional_import("PyPDF2")
        if not pypdf:
            return ""
        reader = pypdf.PdfReader(BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if file_type in {"docx", "doc"}:
        docx = _optional_import("docx")
        if not docx:
            return ""
        document = docx.Document(BytesIO(file_bytes))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)

    return ""


def build_metadata(file_name: str, text: str) -> DocumentMetadata:
    words = [word for word in text.split() if word.strip()]
    return DocumentMetadata(
        name=file_name,
        file_type=file_name.split(".")[-1].lower(),
        word_count=len(words),
        character_count=len(text),
    )


def _contains_keywords(text: str, keywords: List[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def _build_summary(metadata: DocumentMetadata, text: str) -> str:
    if metadata.word_count < 100:
        return (
            "The document is brief and may omit critical architecture details. "
            "Consider expanding scope descriptions, diagrams, and operational considerations."
        )
    if "reference" in text.lower() or "overview" in text.lower():
        return (
            "The document appears to provide an overview of the architecture. "
            "Ensure each major component includes ownership, dependencies, and non-functional requirements."
        )
    return (
        "The document provides a substantive description of the architecture. "
        "Validate that operational readiness, security, and resiliency details are covered." 
    )


def review_document(text: str, metadata: DocumentMetadata) -> Dict[str, object]:
    findings: List[ReviewFinding] = []
    suggestions: List[str] = []
    alignment: List[str] = []

    for check in CHECKS:
        keywords = check["keywords"]
        if not _contains_keywords(text, keywords):
            findings.append(
                ReviewFinding(
                    title=check["title"],
                    severity=str(check["severity"]),
                    observation=(
                        "The document does not mention this topic explicitly. "
                        "This may leave gaps in the architecture review."
                    ),
                    recommendation=str(check["recommendation"]),
                    azure_alignment=str(check["azure_alignment"]),
                )
            )
            suggestions.append(str(check["recommendation"]))
        alignment.append(str(check["azure_alignment"]))

    critical_comments = [
        finding for finding in findings if finding.severity in {"critical", "high"}
    ]

    return {
        "metadata": metadata,
        "summary": _build_summary(metadata, text),
        "critical_comments": critical_comments,
        "improvement_suggestions": suggestions,
        "best_practice_alignment": alignment,
        "findings": findings,
        "next_steps": [
            "Review and confirm non-functional requirements (availability, security, performance).",
            "Add diagrams and data flow documentation for key components.",
            "Align operational processes with Azure Well-Architected Framework pillars.",
        ],
    }
