<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as api from '../api/cart'
import { useAuth } from '../stores/auth'
import { demoMode } from '../utils/runtime'
import { guestCount, guestCartKey, importGuestCart, resetGuestCart } from '../utils/guest-cart'
const auth = useAuth()
const guestItems = ref(guestCount()),
  importMessage = ref('')
function refreshGuestItems(event?: Event) {
  if (!(event instanceof StorageEvent) || event.key === null || event.key === guestCartKey)
    guestItems.value = guestCount()
}
async function importItems() {
  if (busy.value || auth.user?.role !== 'USER') return
  busy.value = true
  importMessage.value = ''
  try {
    const result = await importGuestCart()
    const reasons = new Map<string, number>()
    for (const failure of result.failures)
      reasons.set(failure.message, (reasons.get(failure.message) || 0) + 1)
    importMessage.value = `已导入 ${result.imported} 种商品，游客购物车保留 ${result.remaining} 种。`
    if (reasons.size)
      importMessage.value += Array.from(
        reasons,
        ([reason, count]) => `${reason}（${count} 种）`,
      ).join('；')
    if (result.stopped)
      importMessage.value += '。导入已停止，请先核对账号购物车，再处理保留的游客条目。'
  } catch (e) {
    ElMessage.error((e as Error).message)
  } finally {
    refreshGuestItems()
    await load()
    busy.value = false
  }
}
async function reset() {
  await resetGuestCart()
  await load()
}
const data = ref<api.Cart>(),
  busy = ref(false)
async function load() {
  try {
    data.value = await api.cart()
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
}
async function update(item: api.CartItem, change: { quantity?: number; selected?: boolean }) {
  busy.value = true
  try {
    await api.edit(item.id, change)
  } catch (e) {
    ElMessage.error((e as Error).message)
  } finally {
    await load()
    busy.value = false
  }
}
async function remove(item: api.CartItem) {
  try {
    await api.remove(item.id)
    await load()
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
}
onMounted(() => {
  window.addEventListener('guest-cart-changed', refreshGuestItems)
  window.addEventListener('storage', refreshGuestItems)
  load()
})
onUnmounted(() => {
  window.removeEventListener('guest-cart-changed', refreshGuestItems)
  window.removeEventListener('storage', refreshGuestItems)
})
</script>
<template>
  <div class="page-head">
    <div>
      <h1>{{ auth.user ? '购物车' : '游客购物车' }}</h1>
      <span class="muted">{{
        auth.user
          ? '勾选需要结算的商品，成交价格以下单时为准'
          : '无需注册即可加购、改量、勾选和删除；刷新页面后保留'
      }}</span>
    </div>
    <RouterLink to="/products"><el-button>继续选购</el-button></RouterLink>
  </div>
  <p v-if="!demoMode && auth.user?.role === 'USER' && guestItems" class="notice">
    本浏览器还有游客购物车条目，可手动导入当前账号，同商品数量将合并。
    <el-button :loading="busy" :disabled="busy" @click="importItems">导入游客购物车</el-button>
  </p>
  <p v-if="importMessage" role="status">{{ importMessage }}</p>
  <p v-if="!auth.user" class="notice">
    {{
      demoMode
        ? '当前使用示例商品与库存，所有操作仅保存在本浏览器，不产生真实订单。'
        : '游客购物车仅保存在本浏览器，不占用真实库存；登录后使用独立的账号购物车。'
    }}<el-button text :disabled="busy" @click="reset">清空游客购物车</el-button>
  </p>
  <section class="panel">
    <el-table :data="data?.items || []" empty-text="购物车为空，去选购商品吧"
      ><el-table-column label="结算" width="70"
        ><template #default="{ row }"
          ><el-checkbox
            :model-value="row.selected"
            :disabled="busy"
            @change="(value: unknown) => update(row, { selected: Boolean(value) })"
            :aria-label="'勾选' + row.product_name" /></template></el-table-column
      ><el-table-column label="商品" min-width="180"
        ><template #default="{ row }"
          >{{ row.product_name }}
          <p v-if="row.invalid_reason" class="error-text">
            {{
              row.invalid_reason === 'PRODUCT_NOT_FOUND'
                ? '商品暂不可用'
                : row.invalid_reason === 'PRODUCT_OFF_SHELF'
                  ? '商品已下架'
                  : '当前库存不足'
            }}
          </p></template
        ></el-table-column
      ><el-table-column label="当前单价"
        ><template #default="{ row }">¥{{ row.price }}</template></el-table-column
      ><el-table-column label="数量" width="180"
        ><template #default="{ row }"
          ><el-input-number
            :model-value="row.quantity"
            :disabled="busy"
            :min="1"
            :max="2147483647"
            :precision="0"
            size="small"
            @change="
              (value: number | undefined) => value !== undefined && update(row, { quantity: value })
            " /></template></el-table-column
      ><el-table-column prop="available" label="可售量" /><el-table-column label="操作" width="90"
        ><template #default="{ row }"
          ><el-button link type="danger" :disabled="busy" @click="remove(row)"
            >删除</el-button
          ></template
        ></el-table-column
      ></el-table
    >
    <div class="page-head" style="margin-top: 28px; margin-bottom: 0">
      <span
        >勾选商品参考总价 <strong class="money">¥{{ data?.selected_total || '0.00' }}</strong></span
      ><RouterLink :to="auth.user ? '/checkout' : { path: '/login', query: { next: '/cart' } }"
        ><el-button type="primary" :disabled="!data?.items.some((i) => i.selected) || busy">{{
          auth.user ? '去结算' : demoMode ? '了解完整交易功能' : '登录后下单'
        }}</el-button></RouterLink
      >
    </div>
  </section>
</template>
