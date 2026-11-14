<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { register } from '../api/identity'
import { ElMessage } from 'element-plus'
const form = reactive({ username: '', password: '', nickname: '', phone: '' }),
  error = ref(''),
  busy = ref(false),
  router = useRouter()
async function submit() {
  busy.value = true
  error.value = ''
  try {
    await register(form)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    busy.value = false
  }
}
</script>
<template>
  <main class="workspace" style="max-width: 640px">
    <RouterLink to="/login">← 返回登录</RouterLink>
    <h1>创建普通用户账号</h1>
    <section class="panel">
      <el-form label-position="top" @submit.prevent="submit"
        ><el-form-item label="用户名（3至32位字母、数字或下划线）"
          ><el-input v-model="form.username" autocomplete="username" /></el-form-item
        ><el-form-item label="密码（8至64字符）"
          ><el-input
            v-model="form.password"
            type="password"
            show-password
            autocomplete="new-password" /></el-form-item
        ><el-form-item label="昵称"
          ><el-input v-model="form.nickname" maxlength="50" /></el-form-item
        ><el-form-item label="联系电话"
          ><el-input v-model="form.phone" maxlength="20"
        /></el-form-item>
        <p v-if="error" class="error-text" role="alert">{{ error }}</p>
        <el-button type="primary" native-type="submit" :loading="busy">注册账号</el-button></el-form
      >
    </section>
  </main>
</template>
