<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { simulate } from '../api/payments'
import type { Order } from '../api/orders'
import { formatTime } from '../utils/format'
const props = defineProps<{ order: Order }>(),
  emit = defineEmits<{ changed: [] }>(),
  busy = ref(false)
async function pay(result: 'SUCCESS' | 'FAILURE') {
  busy.value = true
  try {
    const r = await simulate(props.order.order_id, result)
    ElMessage[r.result === 'SUCCESS' ? 'success' : 'warning'](
      r.result === 'SUCCESS' ? '模拟支付成功' : '模拟失败，订单仍待支付',
    )
    emit('changed')
  } catch (e) {
    ElMessage.error((e as Error).message)
    emit('changed')
  } finally {
    busy.value = false
  }
}
</script>
<template>
  <section class="panel">
    <h3>模拟支付</h3>
    <template v-if="order.payment"
      ><p>支付编号 {{ order.payment.payment_id }}</p>
      <p class="money">¥{{ order.payment.amount }}</p>
      <p class="muted">{{ formatTime(order.payment.paid_at) }}</p></template
    ><template v-else-if="order.status === 'PENDING'"
      ><p>
        应付金额 <strong class="money">¥{{ order.total_amount }}</strong>
      </p>
      <p class="muted">课程模拟操作，选择结果后查看订单状态。</p>
      <el-button type="primary" :loading="busy" @click="pay('SUCCESS')">模拟成功</el-button
      ><el-button :disabled="busy" @click="pay('FAILURE')">模拟失败</el-button></template
    >
    <p v-else class="muted">该订单没有成功支付记录。</p>
  </section>
</template>
