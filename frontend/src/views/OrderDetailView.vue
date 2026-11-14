<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as api from '../api/orders'
import OrderItemsTable from '../components/OrderItemsTable.vue'
import PaymentPanel from '../components/PaymentPanel.vue'
import { states, formatTime } from '../utils/format'
const props = defineProps<{ admin?: boolean }>(),
  route = useRoute(),
  item = ref<api.Order>(),
  error = ref(''),
  busy = ref(false)
async function load() {
  try {
    item.value = await api.order(String(route.params.id), props.admin)
    error.value = ''
  } catch (e) {
    error.value = (e as Error).message
  }
}
async function action(mode: 'cancel' | 'receipt' | 'ship') {
  if (!item.value) return
  try {
    await ElMessageBox.confirm(
      { cancel: '确认取消并释放库存？', receipt: '确认已收到商品？', ship: '确认登记为已发货？' }[
        mode
      ],
      '订单操作',
    )
    busy.value = true
    item.value = await { cancel: api.cancel, receipt: api.receipt, ship: api.ship }[mode](
      item.value.order_id,
    )
    ElMessage.success('订单状态已更新')
  } catch (e) {
    if (e instanceof Error) {
      ElMessage.error(e.message)
      await load()
    }
  } finally {
    busy.value = false
  }
}
watch(() => route.params.id, load, { immediate: true })
</script>
<template>
  <RouterLink :to="admin ? '/admin/orders' : '/orders'">← 返回订单列表</RouterLink>
  <p v-if="error" class="error-text" role="alert">{{ error }}</p>
  <template v-if="item"
    ><div class="page-head" style="margin-top: 24px">
      <div>
        <h1>订单 #{{ item.order_id }}</h1>
        <span class="muted">{{ formatTime(item.created_at) }} · {{ item.username }}</span>
      </div>
      <div class="actions">
        <el-tag size="large">{{ states[item.status] }}</el-tag><template v-if="!admin"
          ><el-button v-if="item.status === 'PENDING'" :disabled="busy" @click="action('cancel')"
            >取消订单</el-button
          ><el-button
            v-if="item.status === 'SHIPPED'"
            type="primary"
            :disabled="busy"
            @click="action('receipt')"
            >确认收货</el-button
          ></template
        ><el-button
          v-else-if="item.status === 'PAID'"
          type="primary"
          :disabled="busy"
          @click="action('ship')"
          >登记发货</el-button
        >
      </div>
    </div>
    <p v-if="item.status === 'PENDING' && !admin" class="notice">
      持续占用库存，请支付或手动取消。
    </p>
    <section class="panel">
      <OrderItemsTable :items="item.items" />
      <p style="text-align: right">
        应付金额 <strong class="money">¥{{ item.total_amount }}</strong>
      </p>
    </section>
    <div class="detail-grid">
      <section class="panel">
        <h3>收货与事件信息</h3>
        <p>{{ item.receiver_name }} · {{ item.receiver_phone }}</p>
        <p>{{ item.receiver_address }}</p>
        <el-divider />
        <p>支付时间：{{ formatTime(item.paid_at) }}</p>
        <p>发货时间：{{ formatTime(item.shipped_at) }}</p>
        <p>完成时间：{{ formatTime(item.completed_at) }}</p>
        <p>取消时间：{{ formatTime(item.cancelled_at) }}</p>
      </section>
      <PaymentPanel v-if="!admin" :order="item" @changed="load" />
      <section v-else class="panel">
        <h3>成功支付</h3>
        <template v-if="item.payment"
          ><p>支付编号 {{ item.payment.payment_id }}</p>
          <p class="money">¥{{ item.payment.amount }}</p>
          <p>{{ formatTime(item.payment.paid_at) }}</p></template
        >
        <p v-else class="muted">无成功支付记录</p>
      </section>
    </div></template
  >
</template>
