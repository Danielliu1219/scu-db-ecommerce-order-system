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
      <span class="brand">川大 · 管理工作台</span
      ><RouterLink to="/admin/catalog">商品分类</RouterLink
      ><RouterLink to="/admin/inventory">库存</RouterLink
      ><RouterLink to="/admin/orders">订单</RouterLink
      ><RouterLink to="/admin/payments">支付</RouterLink
      ><RouterLink to="/admin/statistics">统计</RouterLink
      ><RouterLink to="/admin/users">用户</RouterLink>
      <div class="nav-end">
        <span>{{ auth.user?.nickname }}</span><el-button text style="color: white" @click="logout"
          >退出</el-button
        >
      </div>
    </nav>
  </header>
  <main class="workspace"><RouterView /></main>
</template>
