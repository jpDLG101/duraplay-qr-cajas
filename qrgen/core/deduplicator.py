def deduplicate(identifiers: list[str]) -> tuple[list[str], int]:
    seen = []
    dups = 0
    for identifier in identifiers:
        if identifier in seen:
            dups += 1
        else:
            seen.append(identifier)
    
    return (seen, dups)