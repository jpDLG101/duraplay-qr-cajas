def deduplicate(identifiers: list[str]) -> tuple[list[str], int]:
    seen: set[str] = set()
    unique: list[str] = []
    dups = 0
    for identifier in identifiers:
        if identifier in seen:
            dups += 1
        else:
            seen.add(identifier)
            unique.append(identifier)

    return (unique, dups)
