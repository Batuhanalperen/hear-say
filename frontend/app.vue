<template>
  <div class="app-root">
    <header class="app-header">
      <div class="header-inner">
        <NuxtLink to="/" class="logo">
          <div class="logo-icon-wrap">
            <div class="i-tabler-piano" />
          </div>
          <div class="logo-text">
            <span class="logo-name">hear-say</span>
            <span class="logo-tag">audio → piano MIDI</span>
          </div>
        </NuxtLink>

        <div class="header-actions">
          <a
            class="header-link"
            href="https://github.com/batuhanalperen/hear-say"
            target="_blank"
            rel="noopener noreferrer"
            title="View source on GitHub"
          >
            <div class="i-tabler-brand-github" />
          </a>
          <ThemeToggle />
        </div>
      </div>
    </header>

    <main class="main-content">
      <NuxtPage />
    </main>
  </div>
</template>

<style scoped>
.app-root {
  min-height: 100vh;
  background: var(--bg-base);
  color: var(--text);
}

.app-header {
  border-bottom: 1px solid var(--border);
  background: color-mix(in srgb, var(--bg-raised) 85%, transparent);
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-4) var(--space-6);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.logo-icon-wrap {
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background: var(--accent-bg);
  color: var(--accent);
  font-size: 22px;
  border: 1px solid var(--accent-border);
}

.logo-text {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}

.logo-name {
  font-size: var(--text-md);
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--text);
}

.logo-tag {
  font-size: var(--text-xs);
  color: var(--text-dim);
  font-family: "JetBrains Mono", monospace;
  margin-top: 2px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.header-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  color: var(--text-muted);
  font-size: 18px;
  border: 1px solid var(--border);
  transition: all 0.15s ease;
}

.header-link:hover {
  background: var(--bg-raised);
  color: var(--text);
  border-color: var(--border-strong);
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-8) var(--space-6);
}

@media (max-width: 640px) {
  .logo-tag {
    display: none;
  }
  .header-inner {
    padding: var(--space-3) var(--space-4);
  }
  .main-content {
    padding: var(--space-6) var(--space-4);
  }
}
</style>
