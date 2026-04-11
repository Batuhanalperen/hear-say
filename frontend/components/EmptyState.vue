<script setup lang="ts">
defineProps<{
  title: string;
  description?: string;
  icon?: string;
}>();
</script>

<template>
  <div class="empty">
    <div class="empty-icon">
      <div :class="`i-tabler-${icon || 'music-off'}`" />
    </div>
    <h3 class="empty-title">{{ title }}</h3>
    <p v-if="description" class="empty-desc">{{ description }}</p>
    <slot />
  </div>
</template>

<style scoped>
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-16) var(--space-4);
  text-align: center;
}

.empty-icon {
  width: 56px;
  height: 56px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  background: var(--bg-sunken);
  color: var(--text-dim);
  font-size: 28px;
  margin-bottom: var(--space-2);
}

.empty-title {
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--text);
  margin: 0;
}

.empty-desc {
  font-size: var(--text-sm);
  color: var(--text-muted);
  max-width: 360px;
  margin: 0;
}
</style>
