<script setup lang="ts">
const rows = [
  {
    song: "Mozart — Rondo alla Turca",
    mode: "solo",
    accuracy: 99,
    kind: "great",
  },
  {
    song: "Adele — Someone Like You",
    mode: "full-band",
    accuracy: 99,
    kind: "great",
  },
  {
    song: "Annabel Lee — Up",
    mode: "full-band",
    accuracy: 70,
    kind: "ok",
  },
  {
    song: "Notre-Dame de Paris — Les Sans-Papiers",
    mode: "full-band",
    accuracy: 10,
    kind: "poor",
  },
];
</script>

<template>
  <section class="accuracy">
    <div class="accuracy-header">
      <h2>Measured accuracy</h2>
      <p class="accuracy-sub">
        Real songs we tested. Solo piano and piano-driven ballads are solved.
        Dense orchestral or atmospheric tracks still trip up source separation
        — that's the honest state of the art.
      </p>
    </div>
    <div class="table-wrap">
      <table class="acc-table">
        <thead>
          <tr>
            <th>Song</th>
            <th>Mode</th>
            <th class="num">Accuracy</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.song">
            <td>{{ row.song }}</td>
            <td>
              <span class="mode-pill">{{ row.mode }}</span>
            </td>
            <td class="num">
              <div class="acc-cell">
                <div class="bar">
                  <div
                    class="bar-fill"
                    :class="`kind-${row.kind}`"
                    :style="{ width: `${row.accuracy}%` }"
                  />
                </div>
                <span class="bar-value">~{{ row.accuracy }}%</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.accuracy {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  padding: var(--space-10) 0;
}

.accuracy-header {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  max-width: 640px;
}

.accuracy-header h2 {
  font-size: var(--text-2xl);
  font-weight: 700;
  letter-spacing: -0.02em;
  margin: 0;
}

.accuracy-sub {
  font-size: var(--text-base);
  color: var(--text-muted);
  margin: 0;
}

.table-wrap {
  background: var(--bg-raised);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow-x: auto;
}

.acc-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
}

.acc-table th {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  color: var(--text-dim);
  font-weight: 500;
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--border);
}

.acc-table th.num,
.acc-table td.num {
  text-align: right;
}

.acc-table tr + tr td {
  border-top: 1px solid var(--border);
}

.acc-table td {
  padding: var(--space-4);
  color: var(--text);
}

.mode-pill {
  display: inline-block;
  padding: 2px 8px;
  background: var(--bg-sunken);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-family: "JetBrains Mono", monospace;
  color: var(--text-muted);
}

.acc-cell {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 180px;
}

.bar {
  width: 100px;
  height: 6px;
  background: var(--bg-sunken);
  border-radius: var(--radius-full);
  overflow: hidden;
  flex-shrink: 0;
}

.bar-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 500ms ease;
}

.bar-fill.kind-great {
  background: var(--success);
}
.bar-fill.kind-ok {
  background: var(--warning);
}
.bar-fill.kind-poor {
  background: var(--danger);
}

.bar-value {
  font-family: "JetBrains Mono", monospace;
  font-size: var(--text-sm);
  color: var(--text);
  min-width: 48px;
}

@media (max-width: 640px) {
  .acc-cell {
    min-width: auto;
  }
  .bar {
    width: 60px;
  }
}
</style>
