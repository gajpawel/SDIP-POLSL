from typing import Optional, List, Tuple

def is_collision(
    a_arrival: Optional[int],
    a_departure: Optional[int],
    b_arrival: Optional[int],
    b_departure: Optional[int]
) -> bool:

    def get_segments(arr: Optional[int], dep: Optional[int]) -> List[Tuple[int, int]]:
        if arr is None and dep is None:
            return []
        
        start, end = 0, 0
        if arr is None:
            start, end = dep, dep + 5
        elif dep is None:
            start, end = arr, arr + 5
        else:
            start, end = arr, dep

        if end < start:
            return [(start, 1440), (0, end)]
        
        return [(start, end)]

    def segments_collide(s1: Tuple[int, int], s2: Tuple[int, int]) -> bool:
        return not (s1[1] <= s2[0] or s2[1] <= s1[0])

    segments_a = get_segments(a_arrival, a_departure)
    segments_b = get_segments(b_arrival, b_departure)

    if not segments_a or not segments_b:
        return False

    for seg_a in segments_a:
        for seg_b in segments_b:
            if segments_collide(seg_a, seg_b):
                return True

    return False