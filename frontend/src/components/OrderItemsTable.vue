<script setup lang="ts">
import type { Order } from '../api/orders'
defineProps<{ items: Order['items'] }>()
</script>
<template>
  <el-table :data="items" empty-text="无订单明细"
    ><el-table-column
      prop="product_name"
      label="商品名称（成交快照）"
      min-width="200"
    /><el-table-column label="成交单价"
      ><template #default="{ row }">¥{{ row.unit_price }}</template></el-table-column
    ><el-table-column prop="quantity" label="数量" /><el-table-column label="金额"
      ><template #default="{ row }"
        ><span class="money">¥{{ row.line_amount }}</span></template
      ></el-table-column
    ></el-table
  >
</template>
