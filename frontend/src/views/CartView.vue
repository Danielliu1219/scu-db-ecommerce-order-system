<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as api from '../api/cart'
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
onMounted(load)
</script>
<template>
  <div class="page-head">
    <div>
      <h1>购物车</h1>
      <span class="muted">勾选需要结算的商品，成交价格以下单时为准</span>
    </div>
    <RouterLink to="/products"><el-button>继续选购</el-button></RouterLink>
  </div>
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
            {{ row.invalid_reason === 'PRODUCT_OFF_SHELF' ? '商品已下架' : '当前库存不足' }}
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
          ><el-button link type="danger" @click="remove(row)">删除</el-button></template
        ></el-table-column
      ></el-table
    >
    <div class="page-head" style="margin-top: 28px; margin-bottom: 0">
      <span
        >勾选商品参考总价 <strong class="money">¥{{ data?.selected_total || '0.00' }}</strong></span
      ><RouterLink to="/checkout"
        ><el-button type="primary" :disabled="!data?.items.some((i) => i.selected) || busy"
          >去结算</el-button
        ></RouterLink
      >
    </div>
  </section>
</template>
