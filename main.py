from bbb import run, UI, Limits, Selected


def test_func(
    times: UI[int, Limits(ge=1, le=5)],
    name: str = "World",
    name_limit: UI[str, Limits(min_length=3, max_length=20)] = "User",
    excited: bool = False,
    mood: Selected['happy', 'sad', 'neutral'] = 'neutral',
    mood2: Selected[2, 3, 5] = 3
):
    types_info = ", ".join(f"{k}={type(v).__name__}" for k, v in locals().items())
    excitement = "!" * (3 if excited else 1)
    return f"Hello, {name_limit} the {mood} ({mood2})! " + (f"{'Yay' + excitement} " * times) + f"[{types_info}]"

run(test_func)