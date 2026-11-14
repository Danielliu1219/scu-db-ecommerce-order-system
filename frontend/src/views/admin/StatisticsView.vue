<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as api from '../../api/statistics'
import type { components } from '../../types/api'
import { dateRange, formatTime } from '../../utils/format'
const today = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Shanghai' }).format(new Date())
const dates = ref<string[]>([today.slice(0, 8) + '01', today]),
  monthly = ref<components['schemas']['MonthlySales'][]>([]),
  top = ref<components['schemas']['TopProduct'][]>([]),
  inactive = ref<components['schemas']['InactiveUser'][]>([]),
  cutoff = ref(''),
  effective = ref(''),
  page = ref(1),
  total = ref(0)
async function sales() {
  const range = dateRange(dates.value)
  try {
    const [m, t] = await Promise.all([
      api.monthly({ paid_start: range.start, paid_end: range.end }),
      api.top({ paid_start: range.start, paid_end: range.end }),
    ])
    monthly.value = m
    top.value = t
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
}
async function users(reset = false) {
  if (reset) page.value = 1
  try {
    const r = await api.inactive({
      as_of: reset
        ? cutoff.value
          ? cutoff.value + '+08:00'
          : undefined
        : effective.value || undefined,
      page: page.value,
      page_size: 20,
    })
    inactive.value = r.items
    total.value = r.total
    effective.value = r.as_of
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
}
onMounted(() => {
  sales()
  users(true)
})
</script>
<template>
  <div class="page-head">
    <div>
      <h1>销售与用户统计</h1>
      <span class="muted">销售按成功支付时间统计，用户活跃按订单创建时间判断</span>
    </div>
  </div>
  <section class="panel">
    <form class="toolbar" @submit.prevent="sales">
      <el-date-picker
        v-model="dates"
        type="daterange"
        value-format="YYYY-MM-DD"
        start-placeholder="支付开始日期"
        end-placeholder="结束日期"
      /><el-button type="primary" native-type="submit">查询销售</el-button>
    </form>
    <p class="muted">按所选支付期间汇总，期间覆盖部分月份时，仅代表该期间贡献。</p>
    <h3>月销售额与已支付订单量</h3>
    <el-table :data="monthly" empty-text="所选期间无成功支付"
      ><el-table-column prop="sales_month" label="月份" /><el-table-column
        prop="sales_amount"
        label="销售额（元）" /><el-table-column prop="paid_order_count" label="已支付订单量"
    /></el-table>
    <h3 style="margin-top: 32px">商品销量前10</h3>
    <el-table :data="top" empty-text="所选期间无销量"
      ><el-table-column prop="product_id" label="商品编号" /><el-table-column
        prop="product_name"
        label="当前商品名称" /><el-table-column prop="sold_quantity" label="销量（件）"
    /></el-table>
  </section>
  <section class="panel">
    <h3>近30天未下单普通用户</h3>
    <form class="toolbar" @submit.prevent="users(true)">
      <el-date-picker
        v-model="cutoff"
        type="datetime"
        value-format="YYYY-MM-DDTHH:mm:ss"
        placeholder="截至时刻，留空使用当前时间"
        style="width: 280px"
      /><el-button native-type="submit">查询用户</el-button>
    </form>
    <p class="muted">
      本次截至 {{ formatTime(effective) }}；翻页保持此时刻。含从未下单者，期间取消的订单也算下过单。
    </p>
    <el-table :data="inactive" empty-text="没有符合条件的用户"
      ><el-table-column prop="user_id" label="用户编号" /><el-table-column
        prop="username"
        label="用户名" /><el-table-column prop="nickname" label="昵称" /><el-table-column
        prop="phone"
        label="联系电话" /></el-table
    ><el-pagination
      v-model:current-page="page"
      :total="total"
      :page-size="20"
      layout="prev,pager,next,total"
      @current-change="users()"
    />
  </section>
</template>
