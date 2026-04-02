<template>
  <div
    class="app-loading"
    :class="{
      'app-loading--fullscreen': fullscreen,
      'app-loading--compact': compact
    }"
    role="status"
    aria-live="polite"
  >
    <div class="app-loading__spinner" aria-hidden="true">
      <span class="app-loading__ring app-loading__ring--outer"></span>
      <span class="app-loading__ring app-loading__ring--mid"></span>
      <span class="app-loading__ring app-loading__ring--inner"></span>
    </div>
    <p class="app-loading__label">{{ label }}</p>
  </div>
</template>

<script>
export default {
  name: 'AppLoading',
  props: {
    label: {
      type: String,
      default: 'Loading...'
    },
    fullscreen: {
      type: Boolean,
      default: false
    },
    compact: {
      type: Boolean,
      default: false
    }
  }
}
</script>

<style scoped>
.app-loading {
  display: flex;
  min-height: 220px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 14px;
  color: var(--text);
}

.app-loading--fullscreen {
  position: absolute;
  inset: 0;
  z-index: 6;
  min-height: 0;
  background: radial-gradient(680px 320px at 18% 10%, rgba(63, 140, 255, 0.16), transparent 44%),
    radial-gradient(520px 260px at 80% 0%, rgba(51, 197, 201, 0.12), transparent 40%),
    rgba(3, 10, 28, 0.9);
  backdrop-filter: blur(6px);
}

.app-loading--compact {
  min-height: 140px;
  gap: 10px;
}

.app-loading__spinner {
  position: relative;
  width: 72px;
  height: 72px;
}

.app-loading--compact .app-loading__spinner {
  width: 54px;
  height: 54px;
}

.app-loading__ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 2px solid transparent;
  animation: orbit-spin 1.6s cubic-bezier(0.22, 1, 0.36, 1) infinite;
}

.app-loading__ring--outer {
  border-top-color: rgba(63, 140, 255, 0.96);
  border-right-color: rgba(63, 140, 255, 0.3);
}

.app-loading__ring--mid {
  inset: 10px;
  border-bottom-color: rgba(51, 197, 201, 0.9);
  border-left-color: rgba(51, 197, 201, 0.28);
  animation-direction: reverse;
  animation-duration: 1.2s;
}

.app-loading__ring--inner {
  inset: 21px;
  border-top-color: rgba(222, 239, 255, 0.92);
  border-right-color: rgba(222, 239, 255, 0.22);
  animation-duration: 0.9s;
}

.app-loading__label {
  margin: 0;
  font-size: 14px;
  color: #c5dcfa;
  letter-spacing: 0.06em;
}

.app-loading--compact .app-loading__label {
  font-size: 13px;
}

@keyframes orbit-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
