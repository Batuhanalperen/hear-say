<script setup lang="ts">
/**
 * Sheet music view — OpenSheetMusicDisplay renderer with real PDF export.
 *
 * OSMD is configured with `pageFormat: "A4_P"` so the rendered SVGs have
 * A4 dimensions and automatic page breaks. PDF export converts each rendered
 * SVG into a page via jsPDF + svg2pdf.js (lazy-imported on first click).
 */
import { OpenSheetMusicDisplay } from "opensheetmusicdisplay";

const props = defineProps<{
  musicXmlUrl: string | null;
  title?: string;
}>();

const container = ref<HTMLDivElement | null>(null);
const loading = ref(false);
const exporting = ref(false);
const error = ref<string | null>(null);
let osmd: OpenSheetMusicDisplay | null = null;

async function render() {
  if (!container.value || !props.musicXmlUrl) return;
  loading.value = true;
  error.value = null;

  try {
    if (!osmd) {
      osmd = new OpenSheetMusicDisplay(container.value, {
        autoResize: true,
        backend: "svg",
        pageFormat: "A4_P",
        drawTitle: false,
        drawSubtitle: false,
        drawComposer: false,
        drawCredits: false,
        drawingParameters: "default",
      });
    }

    const res = await fetch(props.musicXmlUrl);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const xml = await res.text();
    await osmd.load(xml);
    osmd.render();
  } catch (err) {
    error.value = (err as Error).message;
    console.error("OSMD render error:", err);
  } finally {
    loading.value = false;
  }
}

async function exportPdf() {
  if (!container.value) return;
  exporting.value = true;
  error.value = null;

  try {
    const [{ jsPDF }, svg2pdfModule] = await Promise.all([
      import("jspdf"),
      import("svg2pdf.js"),
    ]);
    const svg2pdf = (svg2pdfModule as any).svg2pdf || (svg2pdfModule as any).default;

    const svgs = Array.from(
      container.value.querySelectorAll<SVGElement>("svg"),
    );
    if (svgs.length === 0) {
      throw new Error("Nothing to export — sheet music has not rendered yet.");
    }

    // A4 portrait: 210 mm x 297 mm
    const pdf = new jsPDF({
      unit: "mm",
      format: "a4",
      orientation: "portrait",
    });

    for (let i = 0; i < svgs.length; i++) {
      if (i > 0) pdf.addPage();
      // svg2pdf reads the SVG's width/height/viewBox to scale into the given box.
      // OSMD's A4_P format emits SVGs sized for A4 proportions already.
      await svg2pdf(svgs[i], pdf, {
        x: 0,
        y: 0,
        width: 210,
        height: 297,
      });
    }

    const safeTitle = (props.title || "score")
      .replace(/[^a-zA-Z0-9-_ ]/g, "")
      .trim()
      .slice(0, 60) || "score";
    pdf.save(`${safeTitle}.pdf`);
  } catch (err) {
    console.error("PDF export error:", err);
    error.value = (err as Error).message;
  } finally {
    exporting.value = false;
  }
}

onMounted(() => {
  render();
});

watch(
  () => props.musicXmlUrl,
  () => render(),
);

onUnmounted(() => {
  osmd = null;
});
</script>

<template>
  <div class="sheet-view">
    <div v-if="!musicXmlUrl" class="empty-msg">
      No MusicXML available for this level.
    </div>
    <template v-else>
      <div class="sheet-controls">
        <button
          type="button"
          class="btn btn-primary"
          :disabled="loading || exporting || !!error"
          @click="exportPdf"
        >
          <div
            v-if="exporting"
            class="i-tabler-loader-2 animate-spin"
          />
          <div v-else class="i-tabler-file-type-pdf" />
          <span v-if="exporting">Exporting…</span>
          <span v-else>Download PDF</span>
        </button>
        <span class="hint">
          Real A4 pages generated with jsPDF — opens in any PDF viewer.
        </span>
      </div>

      <div v-if="loading" class="loading-msg">Rendering sheet music…</div>
      <div v-else-if="error" class="error-msg">{{ error }}</div>

      <!-- OSMD renders into this container. White background for legibility
           of musical notation in both light and dark themes. -->
      <div class="sheet-frame">
        <div ref="container" class="sheet-container" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.sheet-view {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.sheet-controls {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.sheet-controls .hint {
  font-size: var(--text-xs);
  color: var(--text-dim);
}

.empty-msg,
.loading-msg {
  text-align: center;
  padding: var(--space-16) var(--space-4);
  color: var(--text-dim);
}

.error-msg {
  text-align: center;
  padding: var(--space-8) var(--space-4);
  color: var(--danger);
  background: var(--danger-bg);
  border-radius: var(--radius-md);
}

/* Frame around the white sheet-music page so it sits nicely in dark mode */
.sheet-frame {
  background: var(--bg-sunken);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  overflow: auto;
  max-height: 80vh;
}

.sheet-container {
  background: white;
  color: #000;
  border-radius: var(--radius-md);
  padding: var(--space-4);
  min-height: 300px;
  box-shadow: var(--shadow-md);
}
</style>
