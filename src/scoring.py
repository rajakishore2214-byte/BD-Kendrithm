RULES = [('page_title', 25, 'No HTML title found'),
         ('meta_description', 20, 'No meta description found'),
         ('h1', 15, 'No H1 found'), ('https', 20, 'Homepage uses HTTP'),
         ('contact_signal', 10, 'No obvious contact link found'),
         ('service_signal', 10, 'No obvious product/service wording found')]


def score_findings(findings: dict) -> tuple[int | None, list[str]]:
    if findings.get('inspection_status') != 'Inspected':
        return None, []
    missing = [(points, reason) for key, points, reason in RULES if not findings.get(key)]
    return min(100, sum(points for points, _ in missing)), [reason for _, reason in missing]
