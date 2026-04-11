// Theme composable — thin wrapper around VueUse's useColorMode.
//
// Writes `data-theme="dark|light"` onto the <html> element and persists the
// user's choice to localStorage. On first visit the initial value is "auto",
// which follows the system preference (prefers-color-scheme media query).
export function useTheme() {
  return useColorMode({
    selector: "html",
    attribute: "data-theme",
    modes: {
      light: "light",
      dark: "dark",
    },
    storageKey: "hear-say-theme",
    initialValue: "auto",
    emitAuto: true,
  });
}
