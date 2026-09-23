<script setup>
defineProps({ name: { type: String, required: true } })
</script>

<template>
  <svg class="icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <template v-if="name === 'close'"><path d="m6 6 12 12M18 6 6 18" /></template>
    <template v-if="name === 'copy'"><rect x="8" y="8" width="12" height="13" rx="2" /><path d="M15 8V3H3v13h5" /></template>
    <template v-if="name === 'check'"><path d="m5 12 4 4L19 6" /></template>
    <template v-if="name === 'info'"><circle cx="12" cy="12" r="9" /><path d="M12 11v6m0-10h.01" /></template>
    <template v-if="name === 'smile' || name === 'frown'"><circle cx="12" cy="12" r="9" /><path d="M8 9h.01M16 9h.01" /><path v-if="name === 'smile'" d="M7.5 14q4.5 6 9 0" /><path v-else d="M8 17q4-5 8 0" /></template>
    <template v-if="name === 'bubble'">
      <path d="M5.2 5.8h13.6v9.4H11l-4.7 3.4.8-3.4H5.2z" />
      <path d="M9 10.5h.01M12 10.5h.01M15 10.5h.01" />
    </template>
    <template v-else-if="name === 'pin'">
      <path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z" /><circle cx="12" cy="10" r="2.2" />
    </template>
    <template v-else-if="name === 'chevron'"><path d="m9 6 6 6-6 6" /></template>
    <template v-else-if="name === 'search'"><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4 4" /></template>
    <template v-else-if="name === 'spark'"><path d="M12 2.8c.6 4.7 2.7 6.8 7.4 7.4-4.7.6-6.8 2.7-7.4 7.4-.6-4.7-2.7-6.8-7.4-7.4C9.3 9.6 11.4 7.5 12 2.8Z" /><path d="M19.2 15.3c.2 1.7 1 2.5 2.7 2.7-1.7.2-2.5 1-2.7 2.7-.2-1.7-1-2.5-2.7-2.7 1.7-.2 2.5-1 2.7-2.7Z" /></template>
    <template v-else-if="name === 'upload'"><path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5" /><path d="M5 14v5h14v-5" /></template>
    <template v-else-if="name === 'download'"><path d="M12 4v11m0 0 4-4m-4 4-4-4" /><path d="M5 19h14" /></template>
    <template v-else-if="name === 'home'"><path d="m3.5 11 8.5-7 8.5 7" /><path d="M6 9.5V20h12V9.5M10 20v-6h4v6" /></template>
    <template v-else-if="name === 'chart'"><path d="M5 20V10m7 10V4m7 16v-7" /></template>
    <template v-else-if="name === 'store'"><path d="M4 9h16l-1.5-5h-13z" /><path d="M5 9v11h14V9M9 20v-6h6v6" /><path d="M4 9c0 2 3 2 4 0 1 2 3 2 4 0 1 2 3 2 4 0 1 2 4 2 4 0" /></template>
    <template v-else-if="name === 'alert'"><path d="M12 4 3.5 20h17z" /><path d="M12 9v5m0 3h.01" /></template>
    <template v-else-if="name === 'filter'"><path d="M4 6h16M7 12h10m-7 6h4" /></template>
    <template v-else-if="name === 'arrow'"><path d="M5 12h14m-5-5 5 5-5 5" /></template>
    <template v-else-if="name === 'truck'"><path d="M3 6h11v10H3zM14 10h4l3 3v3h-7z" /><circle cx="7" cy="18" r="2" /><circle cx="18" cy="18" r="2" /></template>
    <template v-else-if="name === 'bowl'"><path d="M4 10h16c0 5-3 8-8 8s-8-3-8-8Z" /><path d="M7 6c0-2 2-2 2-4m3 4c0-2 2-2 2-4m3 4c0-2 2-2 2-4M8 21h8" /></template>
    <template v-else-if="name === 'box'"><path d="m4 7 8-4 8 4-8 4z" /><path d="M4 7v10l8 4 8-4V7M12 11v10" /></template>
    <template v-else-if="name === 'wallet'"><path d="M4 6h14v13H4z" /><path d="M4 9h14m0 3h3v5h-3M16 14.5h.01" /></template>
    <template v-else-if="name === 'service'"><circle cx="12" cy="8" r="3" /><path d="M5 20c.6-4 3-6 7-6s6.4 2 7 6M4 8a8 8 0 0 1 16 0M4 8v4h3V8m10 0v4h3V8" /></template>
    <template v-else-if="name === 'database'"><ellipse cx="12" cy="5" rx="7" ry="3" /><path d="M5 5v6c0 1.7 3.1 3 7 3s7-1.3 7-3V5M5 11v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6" /></template>
    <template v-else-if="name === 'brain'"><path d="M9 5a3 3 0 0 0-5 2.2A3 3 0 0 0 4.5 12 3 3 0 0 0 9 16v3M15 5a3 3 0 0 1 5 2.2 3 3 0 0 1-.5 4.8 3 3 0 0 1-4.5 4v3M9 5c0-2 1.2-3 3-3s3 1 3 3v14H9V5Z" /><path d="M7 9h2m6 0h2M7 15h2m6 0h2M12 6v9" /></template>
    <template v-else-if="name === 'code'"><path d="m9 7-5 5 5 5m6-10 5 5-5 5M14 4l-4 16" /></template>
  </svg>
</template>
