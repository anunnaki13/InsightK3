from pathlib import Path

from services.excel_audit_source import REPO_ROOT, render_excel_knowledge_base_markdown


OUTPUT_FILE = REPO_ROOT / "knowledge-base-smk3-166-kriteria.md"


def main() -> None:
    OUTPUT_FILE.write_text(render_excel_knowledge_base_markdown(), encoding="utf-8")
    print(f"Wrote knowledge base markdown from Excel: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
