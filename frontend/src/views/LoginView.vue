<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '../stores/auth'
import { demoMode } from '../utils/runtime'
const form = reactive({ username: '', password: '' }),
  error = ref(''),
  busy = ref(false),
  auth = useAuth(),
  router = useRouter(),
  route = useRoute()
async function submit() {
  if (demoMode) return
  error.value = ''
  busy.value = true
  try {
    await auth.signIn(form.username, form.password)
    const next = String(route.query.next || '')
    await router.push(
      next.startsWith('/') && !next.startsWith('//')
        ? next
        : auth.user?.role === 'ADMIN'
          ? '/admin/users'
          : '/profile',
    )
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    busy.value = false
  }
}
</script>
<template>
  <div class="auth-shell">
    <aside class="auth-aside">
      <span>四川大学 · 数据库系统原理</span>
      <div>
        <p>第20组 / 课程设计</p>
        <h1>从商品选购，<br />到每一笔订单。</h1>
        <p>商品、库存、订单与支付，在同一条业务链路中协同。</p>
      </div>
      <small>电商订单管理系统 · 2026</small>
    </aside>
    <section class="auth-card">
      <p class="muted">欢迎回来</p>
      <h2>{{ demoMode ? '无需注册，即刻体验' : '登录工作空间' }}</h2>
      <p class="muted">
        {{
          demoMode
            ? '公开展示提供商品浏览和游客购物车。真实账号、下单和支付请在完整系统中测试。'
            : '使用普通用户或预置管理员账号登录'
        }}
      </p>
      <RouterLink v-if="demoMode" to="/products"
        ><el-button type="primary">进入游客体验</el-button></RouterLink
      >
      <el-form v-else label-position="top" @submit.prevent="submit"
        ><el-form-item label="用户名"
          ><el-input
            v-model="form.username"
            autocomplete="username"
            aria-label="用户名" /></el-form-item
        ><el-form-item label="密码"
          ><el-input
            v-model="form.password"
            type="password"
            show-password
            autocomplete="current-password"
            aria-label="密码"
        /></el-form-item>
        <p v-if="error" role="alert" class="error-text">{{ error }}</p>
        <el-button type="primary" native-type="submit" :loading="busy" style="width: 100%"
          >登录</el-button
        ></el-form
      >
      <p v-if="!demoMode" class="muted">
        还没有账号？<RouterLink to="/register">注册普通用户</RouterLink>
      </p>
      <RouterLink to="/products" class="auth-guest-link">{{
        demoMode ? '返回商品目录' : '暂不注册，以游客身份体验'
      }}</RouterLink>
    </section>
  </div>
</template>
