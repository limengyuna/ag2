<script setup lang="ts">
/**
 * 通用骨架屏组件
 *
 * 用法：
 *   <Skeleton class="h-4 w-32" />               单条
 *   <SkeletonList :rows="5" item-class="h-12" /> 列表
 *
 * 使用浅灰底和 shimmer 动画表示加载状态。
 */
defineProps<{
  rounded?: boolean   // 是否完全圆形（适合头像）
}>()
</script>

<template>
  <div
    class="skeleton-shimmer bg-gray-200 dark:bg-gray-800"
    :class="rounded ? 'rounded-full' : 'rounded-md'"
  />
</template>

<style scoped>
.skeleton-shimmer {
  position: relative;
  overflow: hidden;
}
.skeleton-shimmer::after {
  content: '';
  position: absolute;
  inset: 0;
  transform: translateX(-100%);
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.6) 50%,
    transparent 100%
  );
  animation: shimmer 1.4s infinite;
}
@keyframes shimmer {
  100% { transform: translateX(100%); }
}
</style>
