<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { orders, type Order } from '../api/orders'
import { states, formatTime, dateRange } from '../utils/format'
const props = defineProps<{ admin?: boolean }>(),
  rows = ref<Order[]>([]),
  total = ref(0),
  dates = ref<string[]>([]),
  filters = reactive({ order_id: '', user_id: '', status: '', page: 1, page_size: 20 })
async function load(reset = false) {
  if (reset) filters.page = 1
  const range = dateRange(dates.value)
  try {
    const { order_id, user_id, ...userFilters } = filters
    const r = await orders(
      {
        ...userFilters,
        ...(props.admin ? { order_id, user_id } : {}),
        created_start: range.start,
        created_end: range.end,
      },
      props.admin,
    )
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
      <h1>{{ admin ? '订单管理' : '我的订单' }}</h1>
      <span class="muted">查询订单、商品快照与处理状态</span>
    </div>
    <el-button @click="load()">刷新</el-button>
  </div>
  <p v-if="!admin" class="notice">待支付订单持续占用库存，请支付或手动取消。</p>
  <section class="panel">
    <form class="toolbar" @submit.prevent="load(true)">
      <template v-if="admin"
        ><el-input v-model="filters.order_id" placeholder="订单编号" clearable /><el-input
          v-model="filters.user_id"
          placeholder="用户编号"
          clearable /></template
      ><el-select v-model="filters.status" placeholder="全部状态" clearable
        ><el-option
          v-for="value in ['PENDING', 'PAID', 'SHIPPED', 'COMPLETED', 'CANCELLED']"
          :key="value"
          :value="value"
          :label="states[value]" /></el-select
      ><el-date-picker
        v-model="dates"
        type="daterange"
        value-format="YYYY-MM-DD"
        start-placeholder="下单开始日期"
        end-placeholder="结束日期"
        style="max-width: 320px"
      /><el-button type="primary" native-type="submit">查询</el-button>
    </form>
    <el-table :data="rows" empty-text="没有匹配订单"
      ><el-table-column prop="order_id" label="订单编号" width="130" /><el-table-column
        v-if="admin"
        prop="username"
        label="用户"
      /><el-table-column label="商品" min-width="220"
        ><template #default="{ row }">{{
          row.items
            .map((i: Order['items'][number]) => i.product_name + ' × ' + i.quantity)
            .join('；')
        }}</template></el-table-column
      ><el-table-column label="应付金额" width="140"
        ><template #default="{ row }"
          ><span class="money">¥{{ row.total_amount }}</span></template
        ></el-table-column
      ><el-table-column label="状态" width="100"
        ><template #default="{ row }"
          ><el-tag>{{ states[row.status] }}</el-tag></template
        ></el-table-column
      ><el-table-column label="下单时间" min-width="180"
        ><template #default="{ row }">{{ formatTime(row.created_at) }}</template></el-table-column
      ><el-table-column label="操作" width="100"
        ><template #default="{ row }"
          ><RouterLink :to="(admin ? '/admin/orders/' : '/orders/') + row.order_id"
            ><el-button link>查看详情</el-button></RouterLink
          ></template
        ></el-table-column
      ></el-table
    ><el-pagination
      v-model:current-page="filters.page"
      :total="total"
      :page-size="20"
      layout="prev,pager,next,total"
      @current-change="load()"
    />
  </section>
</template>
