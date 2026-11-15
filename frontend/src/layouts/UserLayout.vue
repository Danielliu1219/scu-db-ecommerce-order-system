<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ShoppingBag, ArrowUpRight, UserRound } from 'lucide-vue-next'
import { useAuth } from '../stores/auth'
import { useRouter } from 'vue-router'
import { demoMode, appBase } from '../utils/runtime'
import { guestCount } from '../utils/guest-cart'
const auth = useAuth(),
  router = useRouter(),
  count = ref(guestCount())
function updateCount() {
  count.value = guestCount()
}
function logout() {
  auth.clear()
  router.push('/products')
}
onMounted(() => window.addEventListener('guest-cart-changed', updateCount))
onUnmounted(() => window.removeEventListener('guest-cart-changed', updateCount))
</script>
<template>
  <header class="nav-shell">
    <nav class="nav-inner" aria-label="主导航">
      <RouterLink to="/products" class="brand" aria-label="电商订单管理系统首页"
        ><span class="brand-symbol"><ShoppingBag :size="22" :stroke-width="1.5" /></span
        ><span>电商订单<span class="brand-sub">ECOMMERCE / SCU</span></span></RouterLink
      >
      <div class="nav-links">
        <RouterLink to="/products">商品目录</RouterLink
        ><RouterLink to="/cart" aria-label="购物车"
          >购物车 <span v-if="!auth.user && count" class="cart-count">{{ count }}</span></RouterLink
        ><RouterLink v-if="auth.user" to="/orders">我的订单</RouterLink>
      </div>
      <div class="nav-end">
        <template v-if="auth.user"
          ><RouterLink to="/profile" class="identity-link"
            ><UserRound :size="16" />{{ auth.user.nickname }}</RouterLink
          ><el-button text @click="logout">退出</el-button></template
        ><template v-else
          ><span class="mode-label">{{ demoMode ? '前端演示' : '游客体验' }}</span
          ><RouterLink to="/login" class="login-link">登录 <ArrowUpRight :size="15" /></RouterLink
        ></template>
      </div>
    </nav>
  </header>
  <main class="workspace"><RouterView /></main>
  <footer class="site-footer">
    <div><span>电商订单管理系统</span><span>四川大学 · 数据库系统原理课程设计</span></div>
    <div>
      <span>{{
        demoMode
          ? '示例数据仅用于体验，不产生真实订单。'
          : '游客购物车仅保存在本浏览器，不会自动合并到账号。'
      }}</span><a :href="appBase + 'image-credits.txt'">图片来源</a>
    </div>
  </footer>
</template>
