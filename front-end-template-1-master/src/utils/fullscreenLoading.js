import Vue from 'vue'
import AppLoading from '@/components/AppLoading.vue'

let loadingVm = null

function destroyLoading() {
  if (!loadingVm) return
  const rootEl = loadingVm.$el
  loadingVm.$destroy()
  if (rootEl && rootEl.parentNode) {
    rootEl.parentNode.removeChild(rootEl)
  }
  loadingVm = null
}

function ensureLoading(label) {
  if (!loadingVm) {
    const LoadingPortal = Vue.extend({
      name: 'FullscreenLoadingPortal',
      data() {
        return {
          label
        }
      },
      render(h) {
        return h('div', { class: 'app-loading-portal' }, [
          h(AppLoading, {
            props: {
              label: this.label,
              fullscreen: true
            }
          })
        ])
      }
    })

    loadingVm = new LoadingPortal()
    loadingVm.$mount()
    document.body.appendChild(loadingVm.$el)
  } else {
    loadingVm.label = label
  }

  return loadingVm
}

export function showFullscreenLoading(label = '正在加载...') {
  const instance = ensureLoading(label)
  let closed = false

  return {
    setText(text) {
      if (!closed && instance) {
        instance.label = text
      }
    },
    close() {
      if (closed) return
      closed = true
      destroyLoading()
    }
  }
}
