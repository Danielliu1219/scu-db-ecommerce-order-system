<script setup lang="ts">
import { ref } from 'vue'
import { payment } from '../../api/payments'
import type { components } from '../../types/api'
import { states, formatTime } from '../../utils/format'
const id = ref(''),
  result = ref<components['schemas']['PaymentQuery']>(),
  error = ref('')
async function load() {
  error.value = ''
  result.value = undefined
  try {
    result.value = await payment(id.value, true)
  } catch (e) {
    error.value = (e as Error).message
  }
}
</script>
<template>
  <div class="page-head">
    <div>
      <h1>支付记录</h1>
      <span class="muted">按订单编号查询唯一成功支付事实</span>
    </div>
  </div>
  <section class="panel">
    <form class="toolbar" @submit.prevent="load">
      <el-input v-model="id" placeholder="订单编号" aria-label="订单编号" /><el-button
        type="primary"
        native-type="submit"
        >查询支付</el-button
      >
    </form>
    <p v-if="error" class="error-text">{{ error }}</p>
    <template v-if="result"
      ><p>订单状态：{{ states[result.order_status] }}</p>
      <el-descriptions v-if="result.payment" border :column="1"
        ><el-descriptions-item label="支付编号">{{
          result.payment.payment_id
        }}</el-descriptions-item
        ><el-descriptions-item label="支付金额">¥{{ result.payment.amount }}</el-descriptions-item
        ><el-descriptions-item label="支付时间">{{
          formatTime(result.payment.paid_at)
        }}</el-descriptions-item></el-descriptions
      ><el-empty v-else description="该订单没有成功支付记录"
    /></template>
  </section>
</template>
