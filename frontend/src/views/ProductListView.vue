<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Search, ArrowDown, RotateCcw } from 'lucide-vue-next'
import { ElMessage } from 'element-plus'
import * as api from '../api/catalog'
import { add } from '../api/cart'
import ProductCard from '../components/ProductCard.vue'
import { demoMode, guestSession } from '../utils/runtime'
import { editorialImage } from '../utils/product-art'
const rows = ref<api.Product[]>([]),
  categories = ref<api.Category[]>([]),
  total = ref(0)
const loading = ref(true),
  error = ref(''),
  adding = ref('')
const filters = reactive({
  keyword: '',
  category_id: '',
  min_price: '',
  max_price: '',
  page: 1,
  page_size: 12,
})
async function load(reset = false) {
  if (reset) filters.page = 1
  loading.value = true
  error.value = ''
  try {
    const result = await api.products(filters)
    rows.value = result.items
    total.value = result.total
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}
function category(id: string) {
  filters.category_id = id
  load(true)
}
function reset() {
  Object.assign(filters, { keyword: '', category_id: '', min_price: '', max_price: '', page: 1 })
  load()
}
function browse() {
  document.getElementById('catalog')?.scrollIntoView({
    behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
  })
}
async function buy(p: api.Product) {
  if (adding.value) return
  adding.value = p.id
  try {
    await add(p.id, 1)
    ElMessage.success(guestSession() ? '已加入游客购物车' : '已加入购物车')
  } catch (e) {
    ElMessage.error((e as Error).message)
  } finally {
    adding.value = ''
  }
}
onMounted(async () => {
  await load()
  try {
    categories.value = await api.categories()
  } catch (e) {
    error.value = (e as Error).message
  }
})
</script>
<template>
  <section class="store-intro" aria-labelledby="store-title">
    <div class="store-intro-copy">
      <span class="eyebrow">为日常，做一点好选择</span>
      <h1 id="store-title">日常所需，<br /><span>有序到手。</span></h1>
      <p>从书桌上的灵感，到生活中的小事。<br />把所需收入购物车，让每一次选购井然有序。</p>
      <a href="#catalog" class="text-action" @click.prevent="browse"
        >浏览商品 <ArrowDown :size="17"
      /></a>
    </div>
    <div class="editorial-photo">
      <img :src="editorialImage" alt="整洁书桌上的笔记本与文具示意" fetchpriority="high" />
      <div class="editorial-label">
        <span>DESK / DAILY / ESSENTIALS</span><span>日常，从有序开始。</span>
      </div>
    </div>
  </section>
  <div class="experience-strip">
    <span class="square-mark" aria-hidden="true"></span
    ><span>{{
      demoMode
        ? '前端展示 · 示例商品与库存'
        : guestSession()
          ? '游客体验 · 无需注册即可选购'
          : '选购空间 · 当前商品与库存'
    }}</span
    ><span class="experience-detail">{{
      guestSession() ? '浏览、筛选、编辑购物车，不占用库存' : '成交价格与可售库存将在下单时重新核对'
    }}</span>
  </div>
  <section id="catalog" class="catalog-section" aria-labelledby="catalog-heading">
    <div class="catalog-heading">
      <h2 id="catalog-heading">商品目录<span> / COLLECTION</span></h2>
      <span class="result-count">{{ total }} 件商品</span>
    </div>
    <div class="category-tabs" aria-label="商品分类">
      <button
        type="button"
        :class="{ active: !filters.category_id }"
        :aria-pressed="!filters.category_id"
        @click="category('')"
      >
        全部商品</button
      ><button
        v-for="c in categories"
        :key="c.id"
        type="button"
        :class="{ active: filters.category_id === c.id }"
        :aria-pressed="filters.category_id === c.id"
        @click="category(c.id)"
      >
        {{ c.name }}
      </button>
    </div>
    <form class="catalog-filters" @submit.prevent="load(true)">
      <el-input
        v-model="filters.keyword"
        :prefix-icon="Search"
        placeholder="搜索商品名称"
        aria-label="搜索商品名称"
        clearable
      />
      <div class="price-filter">
        <label for="min-price">价格</label
        ><el-input
          id="min-price"
          v-model="filters.min_price"
          placeholder="最低价"
          aria-label="最低价"
          inputmode="decimal"
        /><span>至</span
        ><el-input
          v-model="filters.max_price"
          placeholder="最高价"
          aria-label="最高价"
          inputmode="decimal"
        />
      </div>
      <el-button type="primary" native-type="submit" :loading="loading">查询商品</el-button
      ><el-button :icon="RotateCcw" aria-label="重置筛选" @click="reset" />
    </form>
    <div v-if="error" class="inline-error" role="alert">
      <p>{{ error }}</p>
      <el-button @click="load()">重新加载</el-button>
    </div>
    <div v-else-if="loading" class="product-grid" aria-label="正在加载商品">
      <el-skeleton v-for="n in 4" :key="n" animated
        ><template #template
          ><el-skeleton-item
            variant="image"
            style="width: 100%; aspect-ratio: 1" /><el-skeleton-item
            variant="h3"
            style="width: 65%; margin-top: 20px" /></template
      ></el-skeleton>
    </div>
    <div v-else-if="rows.length" class="product-grid">
      <ProductCard v-for="p in rows" :key="p.id" :product="p" :busy="adding === p.id" @add="buy" />
    </div>
    <el-empty v-else description="没有匹配商品，换个条件试试"
      ><el-button @click="reset">查看全部商品</el-button></el-empty
    >
    <el-pagination
      v-if="total > filters.page_size"
      v-model:current-page="filters.page"
      :total="total"
      :page-size="filters.page_size"
      layout="prev,pager,next,total"
      @current-change="load()"
    />
  </section>
</template>
