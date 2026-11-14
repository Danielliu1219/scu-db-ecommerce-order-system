<script setup lang="ts">
import { useAuth } from '../stores/auth'
import { useRouter } from 'vue-router'
const auth = useAuth(),
  router = useRouter()
function logout() {
  auth.clear()
  router.push('/login')
}
</script>
<template>
  <header class="nav-shell">
    <nav class="nav-inner">
      <span class="brand">川大 · 电商订单</span><RouterLink to="/products">选购商品</RouterLink
      ><RouterLink to="/cart">购物车</RouterLink><RouterLink to="/orders">我的订单</RouterLink
      ><RouterLink to="/profile">个人资料</RouterLink>
      <div class="nav-end">
        <span>{{ auth.user?.nickname }}</span><el-button text style="color: white" @click="logout"
          >退出</el-button
        >
      </div>
    </nav>
  </header>
  <main class="workspace"><RouterView /></main>
</template>
