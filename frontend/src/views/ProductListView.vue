<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as api from '../api/catalog'
import { add } from '../api/cart'
const rows = ref<api.Product[]>([]),
  categories = ref<api.Category[]>([]),
  total = ref(0),
  filters = reactive({
    keyword: '',
    category_id: '',
    min_price: '',
    max_price: '',
    page: 1,
    page_size: 20,
  })
async function load(reset = false) {
  if (reset) filters.page = 1
  try {
    const r = await api.products(filters)
    rows.value = r.items
    total.value = r.total
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
}
async function buy(p: api.Product) {
  try {
    await add(p.id, 1)
    ElMessage.success('已加入购物车')
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
}
onMounted(async () => {
  await load()
  try {
    categories.value = await api.categories()
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
})
</script>
<template>
  <div class="page-head">
    <div>
      <h1>选购商品</h1>
      <span class="muted">按名称、分类与价格发现所需商品</span>
    </div>
    <RouterLink to="/cart"><el-button>查看购物车</el-button></RouterLink>
  </div>
  <section class="panel">
    <form class="toolbar" @submit.prevent="load(true)">
      <el-input v-model="filters.keyword" placeholder="商品名称" clearable /><el-select
        v-model="filters.category_id"
        placeholder="全部分类"
        clearable
        ><el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" /></el-select
      ><el-input v-model="filters.min_price" placeholder="最低价" style="width: 120px" /><span
        >至</span
      ><el-input v-model="filters.max_price" placeholder="最高价" style="width: 120px" /><el-button
        type="primary"
        native-type="submit"
        >查询商品</el-button
      >
    </form>
    <el-table :data="rows" empty-text="没有匹配的上架商品"
      ><el-table-column label="商品" min-width="220"
        ><template #default="{ row }"
          ><RouterLink :to="'/products/' + row.id"
            ><strong>{{ row.name }}</strong></RouterLink
          >
          <p class="muted">{{ row.category_name }}</p></template
        ></el-table-column
      ><el-table-column label="售价" width="160"
        ><template #default="{ row }"
          ><span class="money">¥{{ row.price }}</span></template
        ></el-table-column
      ><el-table-column label="可售库存" width="160"
        ><template #default="{ row }">{{ row.available }} 件</template></el-table-column
      ><el-table-column label="操作" width="240"
        ><template #default="{ row }"
          ><RouterLink :to="'/products/' + row.id"><el-button text>查看详情</el-button></RouterLink
          ><el-button type="primary" :disabled="row.available === 0" @click="buy(row)">{{
            row.available ? '加入购物车' : '暂无库存'
          }}</el-button></template
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
