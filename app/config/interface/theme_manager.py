class ThemeManager:
    DEFAULT_THEME_KEY = "dark"

    def __init__(self, palettes: dict):
        self._palettes = palettes

    def get_palette(self, theme_key: str) -> dict:
        if not self._palettes:
            raise ValueError("Список палитр пуст")

        if theme_key in self._palettes:
            return self._palettes[theme_key]

        if self.DEFAULT_THEME_KEY in self._palettes:
            return self._palettes[self.DEFAULT_THEME_KEY]

        first_key = next(iter(self._palettes))
        return self._palettes[first_key]

    def get_theme_options(self) -> list[tuple[str, str]]:
        return [
            (key, palette.get("name", key)) for key, palette in self._palettes.items()
        ]

    def get_palettes(self) -> dict:
        return self._palettes
