<template>
  <div class="starry-background">
    <vue-particles
      class="starry-background__layer"
      :color="color"
      :particleOpacity="particleOpacity"
      :particlesNumber="particlesNumber"
      shapeType="circle"
      :particleSize="particleSize"
      :linesColor="linesColor"
      :linesWidth="linesWidth"
      :lineLinked="true"
      :lineOpacity="lineOpacity"
      :linesDistance="linesDistance"
      :moveSpeed="moveSpeed"
      :hoverEffect="hoverEffect"
      hoverMode="grab"
      :clickEffect="clickEffect"
      clickMode="push"
    ></vue-particles>
  </div>
</template>

<script>
export default {
  name: 'StarryBackground',
  props: {
    color: {
      type: String,
      default: '#52a2e4'
    },
    particleOpacity: {
      type: Number,
      default: 0.14
    },
    particlesNumber: {
      type: Number,
      default: 72
    },
    particleSize: {
      type: Number,
      default: 3
    },
    linesColor: {
      type: String,
      default: '#8DD1FE'
    },
    linesWidth: {
      type: Number,
      default: 1
    },
    lineOpacity: {
      type: Number,
      default: 0.2
    },
    linesDistance: {
      type: Number,
      default: 150
    },
    moveSpeed: {
      type: Number,
      default: 1.6
    },
    hoverEffect: {
      type: Boolean,
      default: true
    },
    clickEffect: {
      type: Boolean,
      default: false
    }
  }
}
</script>

<style>
.starry-background {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.starry-background__layer {
  width: 100%;
  height: 100%;
}

.starry-background #particles-js {
  width: 100%;
  height: 100%;
}

.starry-background canvas {
  opacity: 1;
}
</style>
