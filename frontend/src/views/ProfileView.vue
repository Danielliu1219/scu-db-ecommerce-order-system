<script setup lang="ts">
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuth } from '../stores/auth'
import * as api from '../api/identity'
const auth = useAuth(),
  form = reactive({ nickname: auth.user?.nickname || '', phone: auth.user?.phone || '' }),
  pwd = reactive({ old_password: '', new_password: '' })
async function save() {
  try {
    auth.user = await api.profile(form)
    ElMessage.success('资料已保存')
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
}
async function change() {
  try {
    await api.password(pwd)
    pwd.old_password = ''
    pwd.new_password = ''
    ElMessage.success('密码已修改')
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
}
</script>
<template>
  <div class="page-head">
    <div>
      <h1>个人资料</h1>
      <span class="muted">{{ auth.user?.username }} · 普通用户</span>
    </div>
  </div>
  <section class="panel">
    <h3>基本资料</h3>
    <el-form label-width="90px" @submit.prevent="save"
      ><el-form-item label="昵称"><el-input v-model="form.nickname" maxlength="50" /></el-form-item
      ><el-form-item label="联系电话"><el-input v-model="form.phone" maxlength="20" /></el-form-item
      ><el-button type="primary" native-type="submit">保存资料</el-button></el-form
    >
  </section>
  <section class="panel">
    <h3>修改密码</h3>
    <el-form label-width="90px" @submit.prevent="change"
      ><el-form-item label="原密码"
        ><el-input
          v-model="pwd.old_password"
          type="password"
          autocomplete="current-password" /></el-form-item
      ><el-form-item label="新密码"
        ><el-input
          v-model="pwd.new_password"
          type="password"
          autocomplete="new-password" /></el-form-item
      ><el-button native-type="submit">修改密码</el-button></el-form
    >
  </section>
</template>
