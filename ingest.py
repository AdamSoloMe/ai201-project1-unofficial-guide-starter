"""
Fetches Rate My Professors reviews for CS professors at a given university
and saves structured text documents to documents/.

Change SCHOOL_NAME to your university before running.
Run once before embed.py.
"""

import os
import base64
import time
import requests

SCHOOL_NAME = "CUNY Queens College"  # Change to your university
DEPARTMENT_NAME = "Computer Science"
MAX_PROFESSORS = 15            # Fetch up to this many professors with ratings
MAX_REVIEWS_PER_PROF = 25      # Reviews to pull per professor

GQL_URL = "https://www.ratemyprofessors.com/graphql"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Content-Type": "application/json",
    "Authorization": "Basic dGVzdDp0ZXN0",
    "Origin": "https://www.ratemyprofessors.com",
    "Referer": "https://www.ratemyprofessors.com/",
}


def gql(query: str, variables: dict) -> dict:
    resp = requests.post(
        GQL_URL,
        json={"query": query, "variables": variables},
        headers=HEADERS,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("errors"):
        raise ValueError(data["errors"][0]["message"])
    return data["data"]


def find_school(name: str) -> tuple[str, str, list[dict]]:
    """Returns (encoded_school_id, display_name, departments_list)."""
    data = gql(
        """
        query NewSearchSchoolsQuery($query: SchoolSearchQuery!) {
          newSearch {
            schools(query: $query) {
              edges { node { id name city state departments { id name } } }
            }
          }
        }
        """,
        {"query": {"text": name}},
    )
    edges = data["newSearch"]["schools"]["edges"]
    if not edges:
        raise ValueError(f"No school found for '{name}'")
    node = edges[0]["node"]
    display = f"{node['name']} ({node['city']}, {node['state']})"
    return node["id"], display, node["departments"]


def get_department_id(departments: list[dict], dept_name: str) -> str:
    """Finds the department whose name contains dept_name and returns its encoded ID."""
    for d in departments:
        if dept_name.lower() in d["name"].lower():
            # RMP expects base64("Department-{numeric_id}")
            return base64.b64encode(f"Department-{d['id']}".encode()).decode()
    raise ValueError(f"Department '{dept_name}' not found. Available: {[d['name'] for d in departments]}")


def search_professors(school_id: str, dept_id: str, count: int) -> list[dict]:
    data = gql(
        """
        query TeacherSearchPaginationQuery($count: Int!, $query: TeacherSearchQuery!) {
          search: newSearch {
            teachers(query: $query, first: $count) {
              edges {
                node {
                  id legacyId firstName lastName department
                  avgRating numRatings avgDifficulty wouldTakeAgainPercent
                }
              }
            }
          }
        }
        """,
        {
            "count": count,
            "query": {"schoolID": school_id, "departmentID": dept_id},
        },
    )
    return [
        e["node"]
        for e in data["search"]["teachers"]["edges"]
        if e["node"]["numRatings"] > 0
    ]


def fetch_reviews(teacher_id: str, count: int) -> list[dict]:
    data = gql(
        """
        query RatingsListQuery($id: ID!, $count: Int!) {
          node(id: $id) {
            ... on Teacher {
              ratings(first: $count) {
                edges {
                  node {
                    comment class date
                    helpfulRating difficultyRating wouldTakeAgain grade
                  }
                }
              }
            }
          }
        }
        """,
        {"id": teacher_id, "count": count},
    )
    return [
        e["node"]
        for e in data["node"]["ratings"]["edges"]
        if (e["node"].get("comment") or "").strip()
    ]


def format_document(prof: dict, reviews: list[dict], school_display: str) -> str:
    pct = prof["wouldTakeAgainPercent"]
    would_again = f"{pct:.0f}%" if pct >= 0 else "N/A"

    lines = [
        f"Professor: {prof['firstName']} {prof['lastName']}",
        f"Department: {prof['department']}",
        f"School: {school_display}",
        f"Overall Rating: {prof['avgRating']:.1f}/5.0",
        f"Difficulty: {prof['avgDifficulty']:.1f}/5.0",
        f"Would Take Again: {would_again}",
        f"Number of Ratings: {prof['numRatings']}",
        "",
        "--- Student Reviews ---",
        "",
    ]
    for r in reviews:
        comment = (r.get("comment") or "").strip()
        if not comment:
            continue
        course = r.get("class") or "Unknown course"
        date = (r.get("date") or "")[:10]
        rating = r.get("helpfulRating", "?")
        difficulty = r.get("difficultyRating", "?")
        grade = r.get("grade") or ""
        again = (
            "Yes" if r.get("wouldTakeAgain") == 1
            else "No" if r.get("wouldTakeAgain") == 0
            else "N/A"
        )
        lines.append(
            f"Course: {course} | Date: {date} | "
            f"Rating: {rating}/5 | Difficulty: {difficulty}/5 | "
            f"Grade: {grade} | Would take again: {again}"
        )
        lines.append(f'"{comment}"')
        lines.append("")

    return "\n".join(lines)


def main():
    os.makedirs("documents", exist_ok=True)

    print(f"Searching for '{SCHOOL_NAME}'…")
    school_id, school_display, departments = find_school(SCHOOL_NAME)
    print(f"  Found: {school_display}")

    dept_id = get_department_id(departments, DEPARTMENT_NAME)
    print(f"  Department ID for '{DEPARTMENT_NAME}': {dept_id}")

    print(f"\nFetching up to {MAX_PROFESSORS} professors with ratings…")
    professors = search_professors(school_id, dept_id, MAX_PROFESSORS)
    print(f"  Got {len(professors)} professors")

    saved = 0
    for prof in professors:
        full_name = f"{prof['firstName']}_{prof['lastName']}"
        safe_name = "".join(c if c.isalnum() or c == "_" else "" for c in full_name)
        out_path = f"documents/{safe_name}.txt"

        if os.path.exists(out_path):
            print(f"  skip  {full_name}")
            continue

        print(f"  fetch {prof['firstName']} {prof['lastName']} ({prof['numRatings']} ratings)…")
        try:
            reviews = fetch_reviews(prof["id"], MAX_REVIEWS_PER_PROF)
            if not reviews:
                print("    WARN no review text, skipping")
                continue
            url = f"https://www.ratemyprofessors.com/professor/{prof['legacyId']}"
            body = format_document(prof, reviews, school_display)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"Source: {safe_name}\nURL: {url}\n\n{body}")
            print(f"    saved ({len(reviews)} reviews, {len(body):,} chars)")
            saved += 1
        except Exception as exc:
            print(f"    ERROR: {exc}")

        time.sleep(0.8)

    print(f"\nDone. {saved} documents saved to documents/")


if __name__ == "__main__":
    main()
