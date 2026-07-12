<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppBackground from './components/AppBackground.vue'
import SiteNav from './components/SiteNav.vue'
import { scheduleNext } from './composables/useReminder'

const route = useRoute()
const immersive = computed(() => !!route.meta.immersive)
onMounted(() => scheduleNext())
</script>

<template>
  <AppBackground />
  <SiteNav v-if="!immersive" />
  <router-view v-slot="{ Component }">
    <transition name="fade" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
</template>
