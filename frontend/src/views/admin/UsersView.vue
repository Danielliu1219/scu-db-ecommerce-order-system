<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { users, type User } from '../../api/identity'
const filters = reactive({ username: '', phone: '', page: 1, page_size: 20 }),
  rows = ref<User[]>([]),
  total = ref(0)
async function load(reset = false) {
  if (reset) filters.page = 1
  try {
    const r = await users(filters)
    rows.value = r.items
    total.value = r.total
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
}
onMounted(() => load())
</script>
<template>
  <div class="page-head">
    <div>
      <h1>普通用户</h1>
      <span class="muted">查询已注册的普通用户资料</span>
    </div>
    <el-tag>{{ total }} 位用户</el-tag>
  </div>
  <section class="panel">
    <form class="toolbar" @submit.prevent="load(true)">
      <el-input v-model="filters.username" placeholder="用户名关键词" clearable /><el-input
        v-model="filters.phone"
        placeholder="联系电话"
        clearable
      /><el-button type="primary" native-type="submit">查询</el-button>
    </form>
    <el-table :data="rows" empty-text="无匹配用户"
      ><el-table-column prop="id" label="编号" width="100" /><el-table-column
        prop="username"
        label="用户名" /><el-table-column prop="nickname" label="昵称" /><el-table-column
        prop="phone"
        label="联系电话" /><el-table-column
        prop="created_at"
        label="注册时间"
        min-width="220" /></el-table
    ><el-pagination
      v-model:current-page="filters.page"
      :page-size="20"
      :total="total"
      layout="prev,pager,next,total"
      @current-change="load()"
    />
  </section>
</template>
