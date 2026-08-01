from typing import TypedDict


SEMESTER_ORDER = ("SPRING", "SUMMER", "FALL")

SEMESTER_LABELS = {
    "SPRING": "Spring",
    "SUMMER": "Summer",
    "FALL": "Fall",
}


class SemesterData(TypedDict):
    term: str
    term_display: str
    year: int
    label: str
    position: int


def normalize_semester_term(term: str) -> str:
    """
    Convert a semester value into the expected uppercase format.

    Examples:
        spring -> SPRING
        Summer -> SUMMER
        FALL -> FALL
    """
    normalized_term = str(term or "").strip().upper()

    if normalized_term not in SEMESTER_ORDER:
        raise ValueError(
            "Invalid semester term. Allowed values are SPRING, SUMMER and FALL."
        )

    return normalized_term


def get_next_semester(term: str, year: int) -> tuple[str, int]:
    """
    Return the semester immediately after the supplied semester.

    Semester sequence:
        Spring -> Summer -> Fall -> Spring of the following year
    """
    normalized_term = normalize_semester_term(term)
    normalized_year = int(year)

    current_index = SEMESTER_ORDER.index(normalized_term)
    next_index = current_index + 1

    if next_index >= len(SEMESTER_ORDER):
        return SEMESTER_ORDER[0], normalized_year + 1

    return SEMESTER_ORDER[next_index], normalized_year


def get_previous_semester(term: str, year: int) -> tuple[str, int]:
    """
    Return the semester immediately before the supplied semester.

    Semester sequence backwards:
        Spring <- Summer <- Fall <- Spring
    """
    normalized_term = normalize_semester_term(term)
    normalized_year = int(year)

    current_index = SEMESTER_ORDER.index(normalized_term)
    previous_index = current_index - 1

    if previous_index < 0:
        return SEMESTER_ORDER[-1], normalized_year - 1

    return SEMESTER_ORDER[previous_index], normalized_year


def format_semester(term: str, year: int) -> str:
    """
    Return a human-readable semester label.

    Example:
        format_semester("SUMMER", 2026)
        -> "Summer 2026"
    """
    normalized_term = normalize_semester_term(term)
    normalized_year = int(year)

    return f"{SEMESTER_LABELS[normalized_term]} {normalized_year}"


def get_semester_timeline(
    start_term: str,
    start_year: int,
    duration: int = 3,
) -> list[SemesterData]:
    """
    Generate the complete semester timeline.

    Example:
        get_semester_timeline("SUMMER", 2026, 3)

    Returns:
        [
            {
                "term": "SUMMER",
                "term_display": "Summer",
                "year": 2026,
                "label": "Summer 2026",
                "position": 1,
            },
            {
                "term": "FALL",
                "term_display": "Fall",
                "year": 2026,
                "label": "Fall 2026",
                "position": 2,
            },
            {
                "term": "SPRING",
                "term_display": "Spring",
                "year": 2027,
                "label": "Spring 2027",
                "position": 3,
            },
        ]
    """
    normalized_term = normalize_semester_term(start_term)
    normalized_year = int(start_year)
    normalized_duration = int(duration)

    if normalized_duration < 1:
        raise ValueError("Semester duration must be at least 1.")

    timeline: list[SemesterData] = []

    current_term = normalized_term
    current_year = normalized_year

    for position in range(1, normalized_duration + 1):
        timeline.append(
            {
                "term": current_term,
                "term_display": SEMESTER_LABELS[current_term],
                "year": current_year,
                "label": format_semester(current_term, current_year),
                "position": position,
            }
        )

        current_term, current_year = get_next_semester(
            current_term,
            current_year,
        )

    return timeline


def get_end_semester(
    start_term: str,
    start_year: int,
    duration: int = 3,
) -> SemesterData:
    """
    Return the final semester of a duration.

    Example:
        Summer 2026 with duration 3
        -> Spring 2027
    """
    timeline = get_semester_timeline(
        start_term=start_term,
        start_year=start_year,
        duration=duration,
    )

    return timeline[-1]


def get_semester_by_position(
    start_term: str,
    start_year: int,
    position: int,
) -> SemesterData:
    """
    Return a specific semester based on its position.

    Position starts from 1.

    Example:
        Summer 2026, position 2
        -> Fall 2026
    """
    normalized_position = int(position)

    if normalized_position < 1:
        raise ValueError("Semester position must be at least 1.")

    timeline = get_semester_timeline(
        start_term=start_term,
        start_year=start_year,
        duration=normalized_position,
    )

    return timeline[-1]