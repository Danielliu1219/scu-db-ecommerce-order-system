<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../stores/auth'
import { cart, type Cart } from '../api/cart'
import { checkout } from '../api/orders'
import { ApiError } from '../api/client'
import { pending, prepare, savePending, clearPending } from '../utils/checkout'
const auth = useAuth(),
  router = useRouter(),
  user = auth.user!.id,
  form = reactive({ receiver_name: '', receiver_phone: '', receiver_address: '' }),
  data = ref<Cart>(),
  uncertain = ref(false),
  busy = ref(false),
  error = ref('')
onMounted(async () => {
  const old = pending(user)
  if (old) {
    Object.assign(form, {
      receiver_name: old.payload.receiver_name,
      receiver_phone: old.payload.receiver_phone,
      receiver_address: old.payload.receiver_address,
    })
    uncertain.value = old.unknown
  }
  try {
    data.value = await cart()
  } catch (e) {
    error.value = (e as Error).message
  }
})
async function submit() {
  error.value = ''
  busy.value = true
  const body = {
    items: (data.value?.items || [])
      .filter((i) => i.selected)
      .map((i) => ({ cart_item_id: i.id, quantity: i.quantity })),
    ...form,
  }
  try {
    const payload = prepare(user, body)
    savePending(user, { payload, unknown: true })
    uncertain.value = true
    const order = await checkout(payload)
    clearPending(user)
    await router.replace('/orders/' + order.order_id)
  } catch (e) {
    const known = e instanceof ApiError && e.status > 0 && e.status < 500
    if (known) {
      const old = pending(user)
      if (old) savePending(user, { ...old, unknown: false })
      uncertain.value = false
      if ((e as ApiError).code === 'CHECKOUT_TOKEN_CONFLICT') clearPending(user)
    }
    error.value = (e as Error).message
  } finally {
    busy.value = false
  }
}
</script>
<template>
  <div class="page-head">
    <div>
      <h1>确认结算</h1>
      <span class="muted">核对勾选商品并填写本次订单的收货信息</span>
    </div>
    <RouterLink to="/cart">返回购物车</RouterLink>
  </div>
  <p v-if="uncertain" class="notice">
    上次提交结果尚待确认。已保留原结算内容，请点击“确认原提交结果”，期间保持原收货信息与商品不变。
  </p>
  <div class="detail-grid">
    <section class="panel">
      <h3>勾选商品</h3>
      <el-table
        :data="data?.items.filter((i) => i.selected) || []"
        empty-text="当前购物车无勾选条目"
        ><el-table-column prop="product_name" label="商品" /><el-table-column
          prop="quantity"
          label="数量" /><el-table-column prop="price" label="当前单价"
      /></el-table>
      <p class="muted">价格与可售库存将在提交时重新核对。</p>
    </section>
    <section class="panel">
      <h3>收货信息</h3>
      <el-form label-position="top" @submit.prevent="submit"
        ><el-form-item label="收货人"
          ><el-input
            v-model="form.receiver_name"
            :disabled="uncertain"
            maxlength="50" /></el-form-item
        ><el-form-item label="联系电话"
          ><el-input
            v-model="form.receiver_phone"
            :disabled="uncertain"
            maxlength="20" /></el-form-item
        ><el-form-item label="收货地址"
          ><el-input
            v-model="form.receiver_address"
            :disabled="uncertain"
            type="textarea"
            :rows="3"
            maxlength="255"
        /></el-form-item>
        <p v-if="error" class="error-text" role="alert">{{ error }}</p>
        <p>
          参考应付 <strong class="money">¥{{ data?.selected_total || '—' }}</strong>
        </p>
        <el-button
          type="primary"
          native-type="submit"
          :loading="busy"
          :disabled="!uncertain && !data?.items.some((i) => i.selected)"
          >{{ uncertain ? '确认原提交结果' : '提交订单' }}</el-button
        ></el-form
      >
    </section>
  </div>
</template>
