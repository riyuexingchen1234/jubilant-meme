from typing import Any, Dict, List

class ReviewAggregator:
    def aggregate(self, style_review: Dict[str, Any], logic_review: Dict[str, Any], rationality_review: Dict[str, Any]) -> Dict[str, Any]:
        all_issues = []
        fatal = []
        general = []
        suggestions = []
        for review, label in [(style_review, "风格"), (logic_review, "逻辑"), (rationality_review, "合理性")]:
            issues = review.get("issues", [])
            for issue in issues:
                issue["source"] = label
                all_issues.append(issue)
                sev = issue.get("severity", "suggestion")
                if sev == "fatal":
                    fatal.append(issue)
                elif sev == "general":
                    general.append(issue)
                else:
                    suggestions.append(issue)
        if fatal:
            verdict = "rewrite"
        elif len(general) > 5:
            verdict = "revise"
        else:
            verdict = "pass"
        return {
            "verdict": verdict,
            "fatal_issues": fatal,
            "general_issues": general,
            "suggestions": suggestions,
            "all_issues": all_issues,
        }
