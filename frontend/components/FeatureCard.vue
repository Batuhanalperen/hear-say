<script setup lang="ts">
defineProps<{
  icon: string;
  title: string;
  description: string;
}>();
</script>

<template>
  <article class="feature-card">
    <div class="feature-icon">
      <div :class="`i-tabler-${icon}`" />
    </div>
    <h3 class="feature-title">{{ title }}</h3>
    <p class="feature-desc">{{ description }}</p>
  </article>
</template>

<style scoped>
.feature-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-6);
  background: var(--bg-raised);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  transition:
    transform 200ms ease,
    border-color 200ms ease,
    box-shadow 200ms ease;
}

.feature-card:hover {
  transform: translateY(-2px);
  border-color: var(--border-strong);
  box-shadow: var(--shadow-md);
}

.feature-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: var(--accent-bg);
  color: var(--accent);
  font-size: 22px;
  border: 1px solid var(--accent-border);
}

.feature-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text);
  margin: 0;
}

.feature-desc {
  font-size: var(--text-sm);
  color: var(--text-muted);
  line-height: var(--lh-normal);
  margin: 0;
}
</style>
