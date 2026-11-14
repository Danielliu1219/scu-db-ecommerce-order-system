<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as api from '../../api/inventory'
import { submitInventory } from '../../utils/inventory'
import { ApiError } from '../../api/client'
import { formatTime } from '../../utils/format'
const rows = ref<api.Inventory[]>([]),
  total = ref(0),
  filters = reactive({ product_id: '', keyword: '', page: 1, page_size: 20 }),
  current = ref<api.Inventory>(),
  mode = ref<'restock' | 'count'>('restock'),
  quantity = ref(1),
  dialog = ref(false),
  busy = ref(false)
async function load(reset = false) {
  if (reset) filters.page = 1
  const r = await api.inventory(filters)
  rows.value = r.items
  total.value = r.total
}
function open(row: api.Inventory, action: 'restock' | 'count') {
  current.value = { ...row }
  mode.value = action
  quantity.value = action === 'count' ? row.available : 1
  dialog.value = true
}
async function submit() {
  if (!current.value) return
  busy.value = true
  const item = current.value
  try {
    await submitInventory(
      () =>
        mode.value === 'restock'
          ? api.restock(item.product_id, {
              quantity: quantity.value,
              expected_version: item.version,
            })
          : api.count(item.product_id, {
              counted_available: quantity.value,
              expected_version: item.version,
            }),
      () => load(),
    )
    dialog.value = false
    await load()
    ElMessage.success('库存已保存')
  } catch (e) {
    if (
      e instanceof ApiError &&
      (e.code === 'INVENTORY_VERSION_CONFLICT' || e.status === 0 || e.status >= 500)
    ) {
      dialog.value = false
      ElMessage.warning('库存已刷新，请核对最新数量后重新选择操作')
    } else ElMessage.error((e as Error).message)
  } finally {
    busy.value = false
  }
}
onMounted(() => load().catch((e) => ElMessage.error(e.message)))
</script>
<template>
  <div class="page-head">
    <div>
      <h1>库存维护</h1>
      <span class="muted">查询可售量，补货及盘点修正</span>
    </div>
    <el-button @click="load().catch((e) => ElMessage.error(e.message))">刷新库存</el-button>
  </div>
  <p class="notice">
    盘点填写“可售数量”。待支付订单占用只供参考；可售量与待支付占用之和不代表完整实物库存。
  </p>
  <section class="panel">
    <form class="toolbar" @submit.prevent="load(true).catch((e) => ElMessage.error(e.message))">
      <el-input v-model="filters.product_id" placeholder="商品编号" clearable /><el-input
        v-model="filters.keyword"
        placeholder="商品名称"
        clearable
      /><el-button native-type="submit">查询</el-button>
    </form>
    <el-table :data="rows" empty-text="无匹配库存"
      ><el-table-column prop="product_id" label="商品编号" width="100" /><el-table-column
        prop="product_name"
        label="商品"
        min-width="180"
      /><el-table-column prop="available" label="可售量" /><el-table-column
        prop="pending_occupied"
        label="待支付占用"
      /><el-table-column prop="version" label="版本" /><el-table-column
        label="更新时间"
        min-width="180"
        ><template #default="{ row }">{{ formatTime(row.updated_at) }}</template></el-table-column
      ><el-table-column label="操作" width="150"
        ><template #default="{ row }"
          ><el-button link @click="open(row, 'restock')">补货</el-button
          ><el-button link @click="open(row, 'count')">盘点</el-button></template
        ></el-table-column
      ></el-table
    ><el-pagination
      v-model:current-page="filters.page"
      :total="total"
      :page-size="20"
      layout="prev,pager,next,total"
      @current-change="load().catch((e) => ElMessage.error(e.message))"
    />
  </section>
  <el-dialog
    v-model="dialog"
    :title="mode === 'count' ? '盘点可售量' : '补货入库'"
    width="min(480px,94vw)"
    ><p>{{ current?.product_name }} · 当前可售 {{ current?.available }} 件</p>
    <el-form @submit.prevent="submit"
      ><el-form-item :label="mode === 'count' ? '确认后的可售数量' : '本次增加数量'"
        ><el-input-number
          v-model="quantity"
          :min="mode === 'count' ? 0 : 1"
          :max="2147483647"
          :precision="0"
      /></el-form-item>
      <p class="muted">保存时核对页面版本，库存发生变化时须重新确认。</p>
      <el-button type="primary" native-type="submit" :loading="busy">确认保存</el-button></el-form
    ></el-dialog
  >
</template>
